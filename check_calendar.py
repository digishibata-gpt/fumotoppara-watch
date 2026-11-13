輸入 むせびむ
輸入 JSON
輸入 再
ちょう 日付時刻 輸入 日付時刻、ゾーン
たーい たーい たーい
から 劇作家。async_api 輸入 async_playwright

URL = 「https://reserve。fumotoppara。net/reserved/reserved-calendar-list"」
外 = マンガン(「診断」)
外。mkdir(exist_ok=看実)

非同期 def サササ():
    結果 = {
        「checked_at_utc」じゅー: 日付時刻。今(みむしゃく。utc).isoformat(),
        「url」: URL、
        「不明」: 「不明」
    }

    非同有 へ async_playwright() はしつ p:
        ・〜〜 = 得つ p。ちロム。打ちょう(首たし=看客)
        ・・む = たつ みブウザ。たっしゅくん_ペーちゃん(
            ジャジャ=「ja-JP」、
            サ_id=「サ/東了」、
            ・・・・・={「幅」: 1440, 「けさ」: 1100}
        )

        試めん:
            応答 = 得つ ページ。シャワー(
                URL、
                wait_until=「domcontentloaded」、
                サササ=45000
            )
            結果[「http_status」] = 応答。ゆううううう else None
            得つ ページ。wait_for_timeout(12000)

            体 = 得つ ページ。そりょり(「体」).サロンガンガンガンガンガン(サササ=10000)
            結果[「body_excerpt」] = 体[:12000]
            結果[「december_31_visible」てす] = やれやれ(
                再。検索(r"12\s*[/月]\s*31|12月31日|2026[-/]12[-/]31", 体)
            )

            結果[「ゆううううう」] = (
                「・・・_・・・・・」
                むし 結果[「december_31_visible」てす]
                たん以外 「target_not_verified」てす
            )

            得つ ページ。むっつんむっつん(
                サ=カツ(外 / 「よレンー。png」),
                full_page=真実
            )

        以被 例被 いしえ e:
            結果[「よー」] = カツ(e)
            結果[「ゆううううう」] = 「よー」

        たかい:
            得つ みブウザ。近⁄()

    (外 / 「結果。JSON」).write_text(
        JSON。ササササ(結果、_ascii= 確濝すたくちゃんちゃん=2),
        ぶるん=「utf-8」
    )
    印刷(JSON。サササ(結果、_ascii= 確濝すたくちゃんちゃん=2))

非同期。看る(サササ())
