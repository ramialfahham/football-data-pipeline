{#
  The provider sends some names as UTF-8 already read as Latin-1 or Windows-1252. A sequence that
  a wrong decode leaves goes back to its bytes and is read as UTF-8; every other character stays,
  so a string that mixes broken and correct letters repairs whole. Control and invisible characters
  go last, with a space before one at the end: some names keep a stray one after the repair. The
  empty match at the end keeps an empty string empty.

  The leads stop at Latin letters and the punctuation block, because a wider rule rewrites correct
  text: U+00E1, U+0161 and a no-break space are the middle of a real name, so a three-byte sequence
  never continues with a Windows-1252 letter first.
#}
{%- macro repair_garbled_text(text) -%}
{%- set windows_1252 -%}
\x{20AC}\x{201A}\x{0192}\x{201E}\x{2026}\x{2020}\x{2021}\x{02C6}\x{2030}\x{0160}\x{2039}\x{0152}\x{017D}\x{2018}\x{2019}\x{201C}\x{201D}\x{2022}\x{2013}\x{2014}\x{02DC}\x{2122}\x{0161}\x{203A}\x{0153}\x{017E}\x{0178}
{%- endset -%}
{%- set garbled -%}
[\x{00C2}-\x{00CB}][\x{0080}-\x{00BF}{{ windows_1252 }}]|[\x{00E1}\x{00E2}][\x{0080}-\x{00BF}\x{20AC}][\x{0080}-\x{00BF}{{ windows_1252 }}]
{%- endset -%}
{%- set windows_1252_text -%}
\U000020AC\U0000201A\U00000192\U0000201E\U00002026\U00002020\U00002021\U000002C6\U00002030\U00000160\U00002039\U00000152\U0000017D\U00002018\U00002019\U0000201C\U0000201D\U00002022\U00002013\U00002014\U000002DC\U00002122\U00000161\U0000203A\U00000153\U0000017E\U00000178
{%- endset -%}
{%- set byte_text -%}
\x80\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8e\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9e\x9f
{%- endset -%}
regexp_replace(
    (
        select string_agg(if(char_length(piece) > 1, decoded, piece), '' order by piece_position)
        from unnest(regexp_extract_all({{ text }}, r'(?s){{ garbled }}|.|$')) as piece with offset as piece_position,
            unnest([
                safe_convert_bytes_to_string(
                    safe.code_points_to_bytes(to_code_points(translate(piece, '{{ windows_1252_text }}', '{{ byte_text }}')))
                )
            ]) as decoded
    ),
    r'\s*[\p{Cc}\p{Cf}]+$|[\p{Cc}\p{Cf}]',
    ''
)
{%- endmacro %}
