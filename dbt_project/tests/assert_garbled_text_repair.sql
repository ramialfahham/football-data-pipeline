-- Fixed examples of repair_garbled_text: each row fails when the repair of `sent` differs from
-- `shown`. The Latin-1 form, the Windows-1252 form, a stray control character, invisible marks, and
-- correct text that must stay as it is.
with examples as (
    select * from unnest([
        struct('A. MaksimoviÄ\u0087' as sent, 'A. Maksimović' as shown),
        struct('M. LjubiÄ\u008diÄ\u0087', 'M. Ljubičić'),
        struct('K. UrbaÅ\u0084ski', 'K. Urbański'),
        struct('J. PotoÄ\u008dnik', 'J. Potočnik'),
        struct('A. VoitinoviÄ\u008dius', 'A. Voitinovičius'),
        struct('L. JovanoviÄ\u0087', 'L. Jovanović'),
        struct('M. CvetkoviÄ\u0087', 'M. Cvetković'),
        struct('N. Kovač \u008d', 'N. Kovač'),
        struct('D. Pejičić\u0087', 'D. Pejičić'),
        struct('F. KneÅ¾eviÄ‡', 'F. Knežević'),
        struct('Dominik MartinoviÄ‡', 'Dominik Martinović'),
        struct('Alpaslan Ã–ztÃ¼rk', 'Alpaslan Öztürk'),
        struct('Æ\u008f. QarÉ™hmÉ™dov', 'Ə. Qarəhmədov'),
        struct('DavÃ­ðsson', 'Davíðsson'),
        struct('CÃ´te d\'Ivoire', 'Côte d\'Ivoire'),
        struct('N. Lâ\u0080\u0099Huillier', 'N. L’Huillier'),
        struct('Nguyá»\u0085n Sá»¹', 'Nguyễn Sỹ'),
        struct('Y. Kassahâ\u0080\u008eâ\u0080\u008f', 'Y. Kassah'),
        struct('Tomáš Vaclík', 'Tomáš Vaclík'),
        struct('Jürgen Müller', 'Jürgen Müller'),
        struct('Åkesson', 'Åkesson'),
        struct('Plain Name', 'Plain Name'),
        struct('', ''),
        struct(cast(null as string), cast(null as string))
    ])
),

repairs as (
    select
        sent,
        shown,
        {{ repair_garbled_text('sent') }} as repaired
    from examples
)

select
    sent,
    shown,
    repaired
from repairs
where repaired is distinct from shown
