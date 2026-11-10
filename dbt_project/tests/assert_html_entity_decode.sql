-- Fixed examples of decode_html_entities: each row fails when the decode of `sent` differs from
-- `shown`. Each entity in the map, a double escape that decodes once, an entity the map lacks, an
-- ampersand that starts no entity, and text that must stay as it is.
with examples as (
    select * from unnest([
        struct('N. O&apos;Reilly' as sent, "N. O'Reilly" as shown),
        struct('A&apos;Sihan', "A'Sihan"),
        struct('&apos;s-Hertogenbosch', "'s-Hertogenbosch"),
        struct('Inter&amp;Co Stadium', 'Inter&Co Stadium'),
        struct('Boulevard O-&gt;E', 'Boulevard O->E'),
        struct('&lt;b&gt;', '<b>'),
        struct('&quot;Pepe&quot;', '"Pepe"'),
        struct('D&#39;Addario', "D'Addario"),
        struct('D&#x27;Addario', "D'Addario"),
        struct('&amp;apos;', '&apos;'),
        struct('Jos&eacute;', 'Jos&eacute;'),
        struct('AT&T Park', 'AT&T Park'),
        struct('A & B &amp; C', 'A & B & C'),
        struct('Brighton & Hove', 'Brighton & Hove'),
        struct('Jürgen Müller', 'Jürgen Müller'),
        struct('Plain Name', 'Plain Name'),
        struct('', ''),
        struct(cast(null as string), cast(null as string))
    ])
),

decodes as (
    select
        sent,
        shown,
        {{ decode_html_entities('sent') }} as decoded
    from examples
)

select
    sent,
    shown,
    decoded
from decodes
where decoded is distinct from shown
