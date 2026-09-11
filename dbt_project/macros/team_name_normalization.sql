{% macro team_name_key(team_name_expr) -%}
trim(
    regexp_replace(
        regexp_replace(
            regexp_replace(
                lower(
                    normalize(cast({{ team_name_expr }} as string), NFKD)
                ),
                r'[\u0300-\u036f]',
                ''
            ),
            r'[^a-z0-9 ]',
            ' '
        ),
        r'\s+',
        ' '
    )
)
{%- endmacro %}


{#
  URL slug from a display name. Produces `[a-z0-9-]` only, with no leading,
  trailing or doubled hyphen. This is the permanent team URL (#852), so the output
  is user-visible and expensive to change once published -- treat any edit here as
  a URL migration, not a refactor.

  THE RULE:
  fold to the base letter where one exists; expand only where none does.
    u-umlaut HAS a base letter  -> Bayern Munchen  -> bayern-munchen
    sharp-s has NONE            -> Rot-Weiss Essen -> rot-weiss-essen
  Those two are ONE rule, not an inconsistency. Anyone "fixing" the apparent
  mismatch by expanding umlauts to ue/oe/ae would change 17 German clubs' URLs for
  nothing. This is what unidecode and iconv //TRANSLIT do, and what Transfermarkt
  ships.

  Why an explicit map is unavoidable: NFKD decomposes an accented letter into base
  plus combining mark, and the mark-strip below then removes the mark. But the ten
  characters mapped here have NO decomposition, so NFKD leaves them intact and the
  final [^a-z0-9]+ step would DELETE them -- which is the defect this replaces
  (Preussen Munster came out as preuen-munster). Ten lowercase entries cover all
  seventeen affected characters, because lower() folds the uppercase halves
  (verified in BigQuery, not assumed).

  Targets verified against external sources rather than glyph shape, because two
  were wrong on the first attempt:
    schwa       -> a   Sabail FK; Qabala, Shamakhi. NOT e -- a schwa merely LOOKS
                       like an e, and "sebail" is a string that exists nowhere.
    d-with-stroke -> dj  Djokovic, the established ASCII digraph. NOT d.
    sharp-s -> ss · ae-lig -> ae · oe-lig -> oe · thorn -> th (Thor) ·
    eth -> d (Sigurdsson) · o-slash -> o (Odegaard) · l-stroke -> l ·
    dotless-i -> i
  Two classes are DELETED rather than hyphenated, because a hyphen there is wrong:
    format characters (\p{Cf}) -- soft hyphen, LRM, LRE. Invisible in the name, so
      a name carrying one must not gain a visible hyphen.
    apostrophes and quote marks -- O'Neill becomes oneill, which is how it is typed
      and searched, not o-neill.

  The guard for anything this map misses is assert_team_name_slug_alphabet.sql, and
  it checks the INPUT alphabet. A guard on the OUTPUT cannot work: the final
  [^a-z0-9]+ step guarantees the output charset, so an unmapped character is
  silently folded away and an output check could never fail on it.

  Deliberately TWO macros rather than one. A single expression nesting all of this is
  ~18 function calls deep, and SQLFluff aborts with "Maximum parse depth exceeded
  (limit 255)" once the templater expands it -- so the model would lint clean locally
  with the macro unresolved and then fail in CI. Splitting the chain in half, applied
  over two CTE steps, keeps both halves parseable. Found by linting, not by reasoning
  about it.
#}
{% macro slug_prepare(name_expr) -%}
lower(regexp_replace(coalesce(cast({{ name_expr }} as string), ''), r'\p{Cf}', ''))
{%- endmacro %}


{#
  The transliteration map, as DATA rather than nested code. Each character of the
  prepared string is looked up in the map and replaced, or passed through unchanged.

  Written this way for a measured reason, not a stylistic one: a chain of ten nested
  `replace()` calls exceeds SQLFluff's parse-depth limit (255) -- probed, the ceiling is
  about eight nested function calls, because each level costs roughly 28 tree levels. A
  nested chain would therefore have to be split across CTE steps, which would scatter one
  map over several places and invite an edit to half of it. Here all ten pairs sit
  together, and adding an eleventh is one line.

  Takes an expression already run through slug_prepare (lowercased, format characters
  removed), so the map only needs lowercase entries.
#}
{% macro translit_latin(prepared_expr) -%}
(
    select string_agg(coalesce(m.to_chars, ch), '' order by pos)
    from unnest(split({{ prepared_expr }}, '')) as ch with offset as pos
    left join
        unnest([
            struct('ß' as from_char, 'ss' as to_chars),
            struct('æ', 'ae'),
            struct('œ', 'oe'),
            struct('þ', 'th'),
            struct('ð', 'd'),
            struct('đ', 'dj'),
            struct('ø', 'o'),
            struct('ł', 'l'),
            struct('ı', 'i'),
            struct('ə', 'a')
        ]) as m
        on m.from_char = ch
)
{%- endmacro %}


{#
  Second half of the slug pipeline: takes the output of translit_latin and produces
  `[a-z0-9-]` with no leading, trailing or doubled hyphen. Separate from the map above
  only to keep each expression inside SQLFluff's parse-depth limit.
#}
{% macro kebab_slug(ascii_expr) -%}
regexp_replace(
    regexp_replace(
        regexp_replace(
            normalize(coalesce({{ ascii_expr }}, ''), NFKD),
            r'[\x{0027}\x{2018}\x{2019}\x{02BC}\x{00B4}`\p{Mn}]',
            ''
        ),
        r'[^a-z0-9]+',
        '-'
    ),
    r'^-+|-+$',
    ''
)
{%- endmacro %}
