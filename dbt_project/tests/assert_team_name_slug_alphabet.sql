-- The guard on the slug transliteration map, and it deliberately checks the INPUT.
--
-- A guard on the OUTPUT cannot work. The slug pipeline ends in `[^a-z0-9]+ -> '-'`, which
-- GUARANTEES the output is `[a-z0-9-]` whatever went in, so an unmapped character is silently
-- folded away or deleted and an output-shape assertion could never fail on it. The first draft
-- of this PR proposed exactly that guard and it would have asserted nothing.
--
-- So: fail when a source team name contains a letter that will NOT survive the pipeline
-- intact -- one that is neither ASCII after NFKD decomposition and mark-stripping, nor covered
-- by the transliteration map in macros/team_name_normalization.sql. That is the condition
-- under which a name silently loses a character from its URL, which is how
-- `Preussen Munster` became `preuen-munster`.
--
-- When this fails, the fix is to add the character to translit_latin's map with a target
-- verified against an external source of record -- never to widen this test. Two targets were
-- wrong on the first attempt precisely because they were inferred from the glyph.
--
-- Scope is teams, matching what the map is settled for. Player and coach names still carry
-- unmapped residue (Cyrillic homoglyphs, bidi marks), so extending this to them is part of
-- their own slug work, not a silent inheritance.

with import_dim_team as (
    select * from {{ ref('dim_team') }}
),

-- one row per character of each team name, after the same preparation the slug does:
-- format characters removed, lowercased, then NFKD-decomposed with combining marks stripped
exploded as (
    select
        import_dim_team.team_api_id,
        import_dim_team.team_name,
        ch
    from import_dim_team,
        unnest(
            split(
                regexp_replace(
                    normalize(
                        lower(regexp_replace(coalesce(team_name, ''), r'\p{Cf}', '')),
                        nfkd
                    ),
                    r'\p{Mn}',
                    ''
                ),
                ''
            )
        ) as ch
)

select
    team_api_id,
    team_name,
    ch as unmapped_character,
    to_code_points(ch)[offset(0)] as codepoint
from exploded
where ch != ''
-- a letter (so punctuation, digits and spaces are out of scope -- the pipeline turns
-- those into separators on purpose)
and regexp_contains(ch, r'\p{L}')
-- that is not plain ASCII
and not regexp_contains(ch, r'^[a-z0-9]$')
-- and is not one the transliteration map handles
and ch not in ('ß', 'æ', 'œ', 'þ', 'ð', 'đ', 'ø', 'ł', 'ı', 'ə')
