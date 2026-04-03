import sqlite3
import requests
from datetime import datetime, timedelta
from omegaconf import OmegaConf
from typing import Any
from utils.fetcher import Github_Fetcher
from utils.summarizer import Client_Analysis


class Repo_Snapshot:
    def __init__(self, cfg):
        self.db_path = cfg.app.db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS repo_snapshots (
            repo_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            html_url TEXT NOT NULL,
            description TEXT DEFAULT '',
            language TEXT DEFAULT '',
            stars INTEGER NOT NULL,
            snapshot_date TEXT NOT NULL,
            PRIMARY KEY (repo_id, snapshot_date)
        )
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshot_date
        ON repo_snapshots(snapshot_date)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_repo_id
        ON repo_snapshots(repo_id)
        """)

        conn.commit()
        conn.close()

    def save_snapshot(self, repos: list[dict[str, Any]]) -> None:
        """
        闂備礁缍婂褏绱炴繝鍥ч棷闁绘垶顭囬埞宥嗙節闂堟稒顥犻柟鐣屽Т閳藉骞橀姘婵犵數鍋涘Λ宀勫礈濠靛洦鍙忛柛鏇ㄥ灠閻鏌″搴′簼闁伙絽宕湁闁绘娅曠亸顓犵磼閵娿劎绨跨紒鐘崇洴椤㈡洟濡堕崨顓烆劀闂?
        濠电姷顣介埀顒€鍟块埀顒€缍婇幃妯诲緞閹邦剚鐎梺缁橆殔閻楀棛绮婇敃鍌氱閻庢稒蓱鐏忣偊鏌ら崹顐㈢仴妞ゆ柨绻橀獮鎾诲箳閺冣偓閹插ジ姊洪棃鈺勭闁告柨鐭傞獮鍐箻鐎电硶鏋栭梺閫炲苯澧€?snapshot_date)闂備焦鐪归崝宀€鈧凹鍓熼獮鎾诲煛閸涱喖浜楅悷婊勭箘濡叉劕鈹戦崶褜鍤ゅ┑顔筋焾妞存悂寮宠箛娑欑厸闁割偒鍋勬晶顖涖亜閹邦兙鍋㈡鐐查叄楠炴﹢宕橀懠顒佸仹缂傚倸鍊烽悞锕傚箰婵犳碍鍊跺鑸靛姇閺嬩胶绱撻崼銏犘ョ紒澶娿偢閹兘寮撮悙鎼￥濠电偞褰冮敃顏呬繆?
        """
        if not repos:
            return

        conn = self._get_conn()
        cur = conn.cursor()

        # 闂備礁鎲￠懝鐐附閺冨倻鍗氶悗娑櫭欢鐐烘煃鏉炴壆鍔嶇憸鑸劦閺岋綁骞樺Δ鈧崯顐ゆ暜閵夆晜鐓曢柟鐑樻煥閳诲牊绻涢崨顓㈠弰鐎殿噮鍠涢ˇ鎶芥煛閸℃瑥鏋涙鐐村灴椤㈡岸宕卞▎鎴Х闂備礁鎲￠崝鏇犵矓閹绢喖鐤柟鎹愵嚙缁€鍌炴煏婢舵盯妾柣鎾亾闂備浇妗ㄩ懗鑸垫櫠濡も偓閻ｅ灚绗熼埀顒勫极瀹ュ懐鏆嗛柛鏇ㄤ簽缁辨岸姊虹粙璺ㄧ缂佸顕槐鐐碘偓锝庡亜缁剁偤鏌嶉崫鍕偓濠氬汲濞嗘挻鐓熼柨婵嗘閹冲嫭淇婇顐簼缂佸倹甯￠獮妯虹暦閸ャ劎娈ら梺鑽ゅС閻掞箑顭垮Ο鑲╃鐎广儱顦繚?
        snapshot_dates = {repo["snapshot_date"] for repo in repos}
        for snapshot_date in snapshot_dates:
            cur.execute("""
            DELETE FROM repo_snapshots
            WHERE snapshot_date = ?
            """, (snapshot_date,))

        rows = []
        for repo in repos:
            rows.append((
                repo["repo_id"],
                repo["full_name"],
                repo["html_url"],
                repo.get("description", ""),
                repo.get("language", ""),
                repo["stars"],
                repo["snapshot_date"],
            ))

        cur.executemany("""
        INSERT OR REPLACE INTO repo_snapshots
        (repo_id, full_name, html_url, description, language, stars, snapshot_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rows)

        conn.commit()
        conn.close()

    # 濠电儑绲藉ú锔炬崲閸岀偞鍋ら柕濞垮妿閻も偓濡炪倖鍔戦崐鏇烆嚕妤ｅ啯鐓涢柛鎰剁畱閸旀粍绻濋埀顒勬晸閻樿櫕娅栭柣蹇曞仧閸樠囧煝韫囨稒鐓熸い顐墮婵¤櫣绱掗鍝勫闁诡垱妫冮獮姗€鎳犵捄鍝勭畱闂備胶顭堢换鎰板疮閹殿喚鐭嗛悗鍦緢apshot_date濠电偞鍨堕幖鈺呭储閹€鏋旈柟杈剧畱鐎氬鏌嶈閸撴艾顕ラ崟顕呮Щ闂?
    def get_all_snapshot_dates(self) -> list[str]:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT DISTINCT snapshot_date
        FROM repo_snapshots
        ORDER BY snapshot_date DESC
        """)

        dates = [row["snapshot_date"] for row in cur.fetchall()]
        conn.close()
        return dates

    # 闂備礁婀遍弫鎼佸磻閹剧偨鈧帡宕奸弴鐐搭棟闂佸搫顦扮€笛嗐亹閵夆晜鐓熼柟鐐殔鐎氼參鏁嶆径鎰厸?
    def get_latest_snapshot_date(self) -> str | None:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT MAX(snapshot_date) AS snapshot_date
        FROM repo_snapshots
        """)

        row = cur.fetchone()
        conn.close()
        return row["snapshot_date"] if row and row["snapshot_date"] else None

    # 闂備礁缍婂褑銇愰悙鐢电當闁稿本绋撻埢鏃堟煃瑜滈崜娆撳煝鎼淬劌鐏抽柧蹇ｅ亜濞撴劙姊虹紒妯诲瘷闁告洦鍓﹀Σ顖炴⒒?
    def get_previous_snapshot_date(self, current_date: str) -> str | None:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT MAX(snapshot_date) AS snapshot_date
        FROM repo_snapshots
        WHERE snapshot_date < ?
        """, (current_date,))

        row = cur.fetchone()
        conn.close()
        return row["snapshot_date"] if row and row["snapshot_date"] else None

    # 闂備礁婀遍弫鎼佸磻閹剧粯鍋傞柛銉ｅ妿閳绘棃鏌嶈閸撴艾顕ラ崟顖氱厸闁告劏鏅濋弳鐘绘椤愩垺绁╅柛瀣瀹?
    def get_repos_by_snapshot_date(self, snapshot_date: str) -> list[dict[str, Any]]:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT repo_id, full_name, html_url, description, language, stars, snapshot_date
        FROM repo_snapshots
        WHERE snapshot_date = ?
        ORDER BY stars DESC, full_name ASC
        """, (snapshot_date,))

        rows = cur.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # 闂備礁鎼悮顐﹀磿閸欏鐝舵慨妞诲亾鐎殿喖顭烽獮鍥敂閸♀晙绱樺┑鐘灩閻忓牓寮插┑鍡忔灁闁硅揪绲块悿鈧銈嗗姂閸婃洖顕ｆィ鍐╃厱闁归偊鍓氶崳鐑樼節閳ь剚鎷呴悷鎵獮濠殿喗锕╅崜娑樞掑畝鍕厸濠㈣泛妫岄崑鎾绘嚑椤掍礁鐨鹃梺鍦帶閻°劑骞愭繝姘辈闁绘梻鍘х粻鍙夈亜閺冣偓椤戞瑩宕崜浣瑰枑?
    def count_repos_by_snapshot_date(self, snapshot_date: str) -> int:
        """
        缂傚倸鍊烽懗鍫曞窗閺囥埄鏁囬柟闂寸閽冪喖鏌熼柇锔跨敖妞ゅ繐宕…鍧楀垂濞戞瑦鐝旈梺鍦劦閺呯娀骞冮檱椤﹀綊鏌涢敐鍥у幋鐎规洘顨嗗蹇涘Ω閿斿墽鏆㈠┑鐘灱閸╂牠鎳濇ィ鍐╁剭妞ゆ牗绋撻埢鏃€銇勮箛鎾虫殶婵炲鍨介獮?
        """
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM repo_snapshots
        WHERE snapshot_date = ?
        """, (snapshot_date,))

        row = cur.fetchone()
        conn.close()
        return row["cnt"] if row else 0


    def count_common_repos(self, current_date: str, previous_date: str) -> int:
        """
        缂傚倸鍊烽懗鍫曞窗閺囥埄鏁囬柛娑橈功閳绘棃鏌曢崼婵囧櫡濞存粠鍨堕弻娑滅疀閹惧疇鍩為梺璇″枟閹搁箖鍩€椤掍胶鈯曢柨姘節閳ь剟顢旈崼鐔峰壄闂佸憡娲︽禍鐐测枖閵忋倕绠归悗娑櫳戠亸浼存煛閸℃瑥鏋涢柡?
        """
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM repo_snapshots c
        JOIN repo_snapshots p
        ON c.repo_id = p.repo_id
        WHERE c.snapshot_date = ?
        AND p.snapshot_date = ?
        """, (current_date, previous_date))

        row = cur.fetchone()
        conn.close()
        return row["cnt"] if row else 0


    def get_snapshot_comparison_stats(self, current_date: str, previous_date: str) -> dict[str, Any]:
        """
        闂佸搫顦弲婊堝蓟閵娿儍娲冀閵娧€鏋栭梺闈涚墕鐎氫即宕电€ｎ喚鍙撻柛銉ㄦ硾娴滅偤鏌涘▎蹇涘弰鐎殿噮鍣ｆ俊鐑芥晜閽樺鍔梻浣圭湽閸斿瞼鈧凹鍓熼、姘额敊婢惰甯″顕€宕掑鍐幏闂佽崵濮崇拋鏌ュ焵椤掑啫绱︾紒璇叉閺?
        """
        current_count = self.count_repos_by_snapshot_date(current_date)
        previous_count = self.count_repos_by_snapshot_date(previous_date)
        common_count = self.count_common_repos(current_date, previous_date)

        return {
            "current_date": current_date,
            "previous_date": previous_date,
            "current_count": current_count,
            "previous_count": previous_count,
            "common_count": common_count,
            "current_only_count": max(current_count - common_count, 0),
            "previous_only_count": max(previous_count - common_count, 0),
        }
    
    # 闂佽崵濮崇欢銈囨閺囥垺鍋╅悹鍥ф▕閸熷懏銇勯弬璺ㄦ癁闁?
    def get_top_growth_repos(
        self,
        current_date: str,
        previous_date: str,
        top_n: int = 10
    ) -> list[dict[str, Any]]:
        """
        闂佽绨肩徊濠氾綖婢舵劖鍎婃い鏃傛櫕閳绘棃鏌曢崼婵嗩伃闁搞倕顑夐悡顐﹀炊鐠鸿桨绨介梺鍛婄懃闁帮絽顕ｉ鈧俊鐑芥晜閽樺鍔梻浣瑰缁嬫垿鎯屾笟鈧、姗€宕妷褌绗?stars 濠电姭鎷冮崨顓濇闂?Top N
        """
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT
            c.repo_id,
            c.full_name,
            c.html_url,
            c.description,
            c.language,
            c.stars AS current_stars,
            p.stars AS previous_stars,
            (c.stars - p.stars) AS weekly_growth,
            c.snapshot_date AS current_snapshot_date,
            p.snapshot_date AS previous_snapshot_date
        FROM repo_snapshots c
        JOIN repo_snapshots p
          ON c.repo_id = p.repo_id
        WHERE c.snapshot_date = ?
          AND p.snapshot_date = ?
        ORDER BY weekly_growth DESC, current_stars DESC
        LIMIT ?
        """, (current_date, previous_date, top_n))

        rows = cur.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                "repo_id": row["repo_id"],
                "full_name": row["full_name"],
                "html_url": row["html_url"],
                "description": row["description"],
                "language": row["language"],
                "stars": row["current_stars"],
                "previous_stars": row["previous_stars"],
                "weekly_stars": row["weekly_growth"],
                "current_snapshot_date": row["current_snapshot_date"],
                "previous_snapshot_date": row["previous_snapshot_date"],
            })

        return results
    
    def diff_in_weeks_days(self,t1, t2) -> dict:
        format = "%Y-%m-%d"
        t1 = datetime.strptime(t1, format)
        t2 = datetime.strptime(t2, format)
        delta = abs(t2 - t1)
        days = delta.days
        weeks = days // 7
        remain_days = days % 7
        time_delta = {}
        time_delta['days'] = remain_days
        time_delta['weeks'] = weeks
        return time_delta

    
    def get_top_growth_repos_safe(self, current_date, previous_date, top_n: int = 10,
            min_common_ratio: float = 0.7, min_common_count: int = 1,) -> dict[str, Any]:
        """
        闂佽娴烽幊鎾凰囬鐐茬煑闊洦绋掗崑?Top Growth 闂備礁鎼悮顐﹀磿閹绢噮鏁嬫俊銈呮噹杩?

        闂備礁鎲￠悷銉╁磹瑜版帒姹查柣鏃傚劋鐎氭岸鎮楀☉娅虫垿锝為弽顓熺叆?
        - current_date: 闁荤喐绮庢晶妤呭箰閸涘﹥娅犻柣妯挎閻も偓濡炪倖鍔戦崐鏇烆嚕妤ｅ啯鐓涢柛鎰剁畱閸旀粍绻濋埀顒勬晸閻樿櫕娅栧┑鐐村灦椤ㄥ牓鎮峰┑鍠㈠綊鎳栭埡浣囥垽鏌涢…鎴濈仸闁硅櫕鐩、鏃堝礋椤愬秵顨婇弻娑樷枎閹邦喖顫у┑鐐存尭閻栫厧顕ｉ鍕亱闁割偆鍣︾槐姘舵⒑?
        - previous_date: 濠电偞鍨堕幐鎼佹晝閿濆洨鍗氶悗娑欘焽閳绘梹銇勮箛鎾愁仾鐟滆埇鍎甸弻锝夊箻濡も偓鐎氼參鏁嶆径鎰厸闁割偁鍨瑰▍鎰磼鏉堫偊鍝虹紒瀣槸椤撳ジ宕熼鐘测偓鐐烘⒑閸涘﹤绗氶柣鐔村姂瀹曢潧顭ㄩ崼婵堫槷闂侀潧顭堥崕杈╁緤?current_date 濠电偞鍨堕弻銊╊敄閸涱喗娅犻柣妯款嚙鐎氬鏌嶈閸撴艾顭囨繝姘闁绘ê纾弳鐘绘⒑閸濆嫬鏆旈柛搴㈠絻閿?
        - top_n: 闂佸搫顦弲婊堝蓟閵娿儍娲冀椤撶偟顦?N 濠?
        - min_common_ratio: 濠电偞鍨堕幐鍫曞磹閺囥垹桅濠㈣泛顑囬々鏌ユ煏閸繍妲归柤鑼Т闇夐柣妯挎珪鐏忣厾绱掗妸鈺€鎲剧€?/ 闂佸搫顦悧鍡涘疮椤愶附鍎嶆い鎺戝閻掍粙鏌ㄥ┑鍡樺櫡濞存粠鍨伴湁闁绘娅曠亸顓犵磼閵娾晙鎲炬鐐╁亾缂傚倷鐒﹁摫婵?闂備焦鐪归崝宀€鈧凹鍘奸妴鎺楀礈娴ｉ鍓ㄩ棅顐㈡处濮婅危瀹勮埇鈧帒顫濋澶婂壍濡炪倐鏅粻鎴炴櫏?
        - min_common_count: 闂備胶鍘ч崲鏌ュ疮閸ф鍎嶆い鏍ㄧ矋閸熷搫霉閿濆牜娼愮紒鐘冲笒椤潡鎳滄担鍐棟闂佹椿鐓堥崹璺虹暦濡ゅ懎纭€闁绘劖娼欓埀顒€宕湁闁绘娅曠亸顓犵磼閵娾晙鎲鹃柡浣哥Ф娴狅箓鎳為妷銉ュ⒕闂備礁鎲＄敮妤呮偡閵娾晩鏁囩紓浣诡焽閳绘棃寮堕悙鏉戭棆闁荤喐绻堥弻銈団偓鍦Т琚氶梺浼欏瘜閸犳顭?

        闂佸搫顦弲婊堝蓟閵娿儍娲冀椤撶喐娅?
        {
            "ok": bool,
            "message": str,
            "stats": {...},
            "results": [...]
        }
        """
        if current_date is None:
            current_date = self.get_latest_snapshot_date()

        if current_date is None:
            return {
                "ok": False,
                "message": "闂備浇妗ㄩ懗鑸垫櫠濡も偓閻ｅ灚鎷呯憴鍕妳闂佽宕樼亸顏堝储椤掍胶绠鹃悘鐐殿焾婢у弶绻濋埀顒佹媴閸︻収娴勯柣鐘辩绾绢厾绮旈崸妤冨彄闁搞儴娉涙禍鐐烘煕濞嗗繘鍙勭€殿噮鍋婇幃褔宕煎┑鍫涘亰",
                "stats": None,
                "results": [],
            }

        if previous_date is None:
            previous_date = self.get_previous_snapshot_date(current_date)

        if previous_date is None:
            return {
                "ok": False,
                "message": f"当前日期 {current_date} 没有可比较的上一个快照日期",
                "stats": None,
                "results": [],
            }

        stats = self.get_snapshot_comparison_stats(current_date, previous_date)

        current_count = stats["current_count"]
        previous_count = stats["previous_count"]
        common_count = stats["common_count"]

        if current_count == 0:
            return {
                "ok": False,
                "message": f"闁荤喐绮庢晶妤呭箰閸涘﹥娅犻柣妯挎閻も偓濡炪倖鍔戦崐鏇烆嚕妤ｅ啯鐓涢柛鎰剁畱閸旀粍绻濋埀?{current_date} 婵犵數鍋涙径鍥礈濠靛棴鑰垮〒姘ｅ亾鐎殿噮鍋婇幃褔宕煎┑鍫涘亰",
                "stats": stats,
                "results": [],
            }

        if previous_count == 0:
            return {
                "ok": False,
                "message": f"濠电偞鍨堕幐鎼佹晝閿濆洨鍗氶悗娑欘焽閳绘梹銇勮箛鎾愁仾鐟滆埇鍎甸弻锝夊箻濡も偓鐎氼參鏁嶆径鎰厸?{previous_date} 婵犵數鍋涙径鍥礈濠靛棴鑰垮〒姘ｅ亾鐎殿噮鍋婇幃褔宕煎┑鍫涘亰",
                "stats": stats,
                "results": [],
            }

        if common_count < min_common_count:
            return {
                "ok": False,
                "message": (
                    f"两天共同仓库数过少，无法可靠比较："
                    f"common_count={common_count}, min_common_count={min_common_count}"
                ),
                "stats": stats,
                "results": [],
            }

        base_count = min(current_count, previous_count)
        common_ratio = common_count / base_count if base_count > 0 else 0.0
        stats["common_ratio"] = common_ratio

        if common_ratio < min_common_ratio:
            return {
                "ok": False,
                "message": (
                    f"两天共同仓库占比过低，比较结果可能不可靠："
                    f"common_ratio={common_ratio:.2%}, min_common_ratio={min_common_ratio:.2%}"
                    f'common_count={common_count:}'
                ),
                "stats": stats,
                "results": [],
            }

        results = self.get_top_growth_repos(
            current_date=current_date,
            previous_date=previous_date,
            top_n=top_n,
        )
        time_delta = self.diff_in_weeks_days(current_date, previous_date)


        return {
            "ok": True,
            "message": "查询成功",
            "stats": stats,
            "results": results,
            "time_delta": time_delta
        }



    def debug_print_all(self) -> None:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT repo_id, full_name, html_url, description, language, stars, snapshot_date
        FROM repo_snapshots
        ORDER BY snapshot_date DESC, stars DESC
        """)

        rows = cur.fetchall()
        conn.close()

        for row in rows:
            print(dict(row))


if __name__ == '__main__':

    cfg = OmegaConf.load("config.yaml")
    fetcher = Github_Fetcher(cfg)
    snapshoter = Repo_Snapshot(cfg)
    analysier = Client_Analysis(cfg)
    repos = fetcher.fetch_candidate_repos()
    snapshoter.save_snapshot(repos)
    ltst_date = snapshoter.get_latest_snapshot_date()
    all_date = snapshoter.get_all_snapshot_dates()
    # for item in all_date:
    #     print(item)
    diff = snapshoter.get_top_growth_repos_safe()
    for item in diff['results']:
        summary = analysier.get_response(item)

    snapshoter.debug_print_all()
