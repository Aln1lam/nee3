# Combined Documentation

Generated: 2026-05-20T16:33:52.6102278+08:00

## Source: docs\index.md

# neepu 椤圭洰鐭ヨ瘑搴?

娆㈣繋浣跨敤鏈粨搴撶敓鎴愮殑鐭ヨ瘑搴撱€傛枃妗ｅ寘鎷細椤圭洰姒傝銆佸悗绔笌鍓嶇缁撴瀯銆佽矾鐢变笌鏈嶅姟璇︾粏璇存槑銆佸紑鍙戣繍琛屾寚鍗椾笌甯歌闂銆?

蹇€熷紑濮嬶細

- 鍦ㄦ湰鍦版煡鐪嬶紙鎺ㄨ崘浣跨敤 MkDocs + Material 涓婚锛夛細鍙傝浠撳簱鏍圭洰褰曠殑 `mkdocs.yml`銆?
- 鏂囨。涓婚〉浣嶄簬鏈洰褰曚笅鐨勫悇涓?Markdown 鏂囦欢锛屼緥濡?`overview.md`銆乣backend.md`銆乣routes.md` 绛夈€?

鑻ラ渶鍦ㄦ湰鍦版瀯寤虹珯鐐癸紝璇峰弬瑙佷粨搴撴牴鐩綍鐨?`build_docs.ps1`锛堟垨浣跨敤 `mkdocs` 鍛戒护锛夈€?

鐩綍瀵艰埅锛氬弬瑙佺珯鐐逛晶杈规爮锛堝凡鐢?`mkdocs.yml` 閰嶇疆锛夈€?


---

## Source: docs\overview.md

# 姒傝

椤圭洰鏍圭洰褰曚富瑕佸唴瀹癸細

- `backend/`锛氬悗绔湇鍔′笌璺敱瀹炵幇锛團lask / FastAPI 椋庢牸缁撴瀯锛夈€?
- `frontend/`锛氬熀浜?Vite 鐨勫墠绔晫闈紝鍖呭惈 `src/`銆乣public/` 绛夈€?
- `captures/`锛氱綉缁滄祦閲忔姄鍖咃紙PCAP锛夌ず渚嬫暟鎹紝鎸夋寫鎴?鍥㈤槦缁勭粐銆?
- `GZCTF-develop/`锛氱珵璧涙垨骞冲彴鐩稿叧璧勬簮涓庤鏄庛€?
- `scripts/`锛氳繍缁存垨鏌ヨ鑴氭湰锛堝 `query_db.py`锛夈€?

蹇€熼槄璇昏矾寰勶細

- 鍚庣鍏ュ彛涓庨厤缃細鏌ョ湅 `backend/app.py` 涓?`backend/server/config.py`銆?
- 璺敱瀹炵幇锛氭煡鐪?`backend/route/` 涓嬬殑鍚勬ā鍧楋紙濡?`challenges.py`銆乣auth.py`锛夈€?
- 鏈嶅姟灞傦細`backend/server/services/` 涓嬬殑澶氫釜鏈嶅姟锛堝鍣ㄣ€佽瘎鍒嗐€佽皟搴︾瓑锛夈€?


---

## Source: docs\backend.md

# 鍚庣锛堟ā鍧楁瑙堬級

涓昏鐩綍涓庢枃浠讹細

- `backend/app.py`锛氬簲鐢ㄥ叆鍙ｏ紙鍚姩閰嶇疆涓庢墿灞曞垵濮嬪寲锛夈€?
- `backend/route/`锛氳矾鐢卞眰锛屾寜鍔熻兘鍒掑垎锛堣璇併€佹寫鎴樸€侀槦浼嶇瓑锛夈€?
- `backend/server/`锛氬钩鍙扮骇鏈嶅姟涓庨厤缃紙`config.py`銆乣db_models.py`銆乣extensions.py` 绛夛級銆?
- `backend/services/`锛氫笟鍔℃湇鍔″疄鐜帮紙瀹瑰櫒绠＄悊銆佽瘎鍒嗐€佽皟搴︾瓑锛夈€?

瀹氫綅璺敱瀹炵幇锛?

- 璺敱鏂囦欢浣嶄簬 [backend/route](backend/route)銆傚父瑙佹ā鍧楋細`challenges.py`銆乣auth.py`銆乣uploads.py`銆乣teams.py` 绛夈€?

鏃ュ織涓庝腑闂翠欢锛?

- 涓棿浠跺疄鐜板垎涓?`middleware/` 涓?`middleware_refactored/`锛岀敤浜庣紦瀛樸€佸帇缂┿€侀檺娴佷笌瀹夊叏澶勭悊銆?

寤鸿闃呰椤哄簭锛?

1. `backend/app.py`锛堝惎鍔ㄦ祦绋嬶級
2. `backend/server/extensions.py`锛堟墿灞曟敞鍐岋級
3. `backend/route/*.py`锛堝姛鑳借矾鐢憋級
4. `backend/server/services/`锛堟牳蹇冧笟鍔￠€昏緫锛?


---

## Source: docs\frontend.md

# 鍓嶇锛堟ā鍧楁瑙堜笌杩愯锛?

椤圭洰鍓嶇浣嶄簬 `frontend/`锛屽熀浜?Vite锛?

- 鍏ュ彛锛歚frontend/index.html`銆?
- 婧愪唬鐮侊細`frontend/src/`锛坄App.vue`銆佽矾鐢便€佺粍浠躲€佹湇鍔＄瓑锛夈€?
- 渚濊禆涓庤剼鏈細`frontend/package.json`銆?

鏈湴鍚姩锛堝父瑙侊級锛?

```bash
cd frontend
npm install
npm run dev
```

鏋勫缓鐢熶骇鍖咃細

```bash
npm run build
```


---

## Source: docs\development.md

# 寮€鍙戠幆澧冧笌杩愯鎸囧崡

寤鸿鐨勬湰鍦板紑鍙戞楠わ紙Python 鍚庣锛夛細

1. 鍒涘缓骞舵縺娲昏櫄鎷熺幆澧冿細

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 瀹夎渚濊禆锛氬鏋滀粨搴撳惈 `requirements.txt` 鎴?`pyproject.toml`锛岃鎸夋枃浠跺畨瑁咃紱鍚﹀垯鏌ョ湅 `backend/` 涓嬫枃妗ｆ垨婧愮爜澹版槑鐨勪緷璧栥€?

3. 鍚姩鍚庣锛氭煡鐪?`backend/app.py` 浠ヨ幏鍙栬繍琛屾柟寮忥紙WSGI/ASGI锛夈€傚父瑙佸懡浠ょず渚嬶細

```powershell
python backend/app.py
# 鎴?浣跨敤 uvicorn/gunicorn 鍚姩锛堝鏋滀负 ASGI锛?
```

4. 鍚姩鍓嶇锛氬弬瑙?`docs/frontend.md`銆?

娴嬭瘯锛?

```bash
pip install pytest
pytest -q
```

娉ㄦ剰锛氬湪鎵ц鏁版嵁搴撶浉鍏虫搷浣滃墠锛岀‘璁ら厤缃枃浠?`backend/server/config.py` 涓殑杩炴帴淇℃伅銆?


---

## Source: docs\routes.md

# 璺敱绱㈠紩锛堟瑕侊級

璺敱瀹炵幇闆嗕腑鍦?`backend/route/`锛屾枃浠舵寜鍔熻兘鍒嗙粍锛屼笅闈㈠垪鍑轰粨搴撲腑甯歌鐨勮矾鐢辨ā鍧楀強鑱岃矗锛?

- `admin.py`锛氬钩鍙扮鐞嗙浉鍏虫帴鍙ｃ€?
- `articles.py`锛氭枃绔?鍏憡鎺ュ彛銆?
- `attachments.py`锛氶檮浠剁鐞嗐€?
- `auth.py`锛氳璇併€佺櫥褰曘€佷細璇濄€?
- `challenges.py`锛氭寫鎴樺垪琛ㄣ€佽鎯呫€佹彁浜ら€昏緫锛堝綋鍓嶇紪杈戞枃浠讹級銆?
- `container_challenges.py`锛氬熀浜庡鍣ㄧ殑鎸戞垬鎺ュ彛銆?
- `ctf_api.py`銆乣ctf_admin.py`锛氳禌浜嬪疄鏃舵帴鍙ｄ笌绠＄悊銆?
- `teams.py`锛氶槦浼嶇浉鍏虫搷浣溿€?
- `uploads.py`锛氫笂浼犲鐞嗐€?

鏌ユ壘鏌愯矾鐢辩殑瀹炵幇缁嗚妭锛氬湪瀵瑰簲鏂囦欢涓悳绱㈣矾鐢辫楗板櫒锛堝 `@app.route`銆乣@bp.route` 鎴栨鏋跺搴旀爣璁帮級銆?

## 璺敱鏂囦欢娓呭崟锛堝凡鎵弿锛?

- [backend/route/challenges.py](backend/route/challenges.py): 棰樼洰鐩稿叧璺敱锛涘寘鍚幏鍙栭鐩垪琛ㄣ€侀鐩鎯呫€佹彁浜?Flag銆佹帓琛屾銆佹彁绀虹郴缁熴€佷綔寮婃娴嬨€佸鍣ㄥ疄渚嬬鐞嗭紙鍚姩/鍋滄/寤舵椂/鐘舵€侊級銆侀鐩粺璁＄瓑銆傚叧閿鐐圭ず渚嬶細
	- `GET /games/<game_id>/challenges`锛氳幏鍙栫珵璧涢鐩垪琛?
	- `GET /<challenge_id>`锛氶鐩鎯?
	- `POST /<challenge_id>/submit`锛氭彁浜?Flag锛堝惈鍔ㄦ€佸垎鏁般€佽娑插鍔便€佷綔寮婃娴嬶級
	- `POST /<challenge_id>/start-container`锛氬惎鍔ㄩ鐩鍣?
	- `GET /games/<game_id>/scoreboard`锛氳幏鍙栨帓琛屾

- [backend/route/container_challenges.py](backend/route/container_challenges.py): 闈㈠悜瀹瑰櫒鐨勯鐩壒娈婃帴鍙ｏ紙涓?`challenges.py` 浜掕ˉ锛夈€?
- [backend/route/auth.py](backend/route/auth.py): 璁よ瘉銆佺櫥褰曘€丣WT 鐩稿叧鎺ュ彛銆?
- [backend/route/teams.py](backend/route/teams.py): 闃熶紞鍒涘缓/绠＄悊/鎴愬憳閭€璇锋帴鍙ｃ€?
- [backend/route/uploads.py](backend/route/uploads.py): 鏂囦欢涓婁紶涓庨檮浠跺鐞嗐€?
- [backend/route/ctf_api.py](backend/route/ctf_api.py): 姣旇禌瀹炴椂 API 鎺ュ彛锛堥潰鍚戝墠绔殑姹囨€讳笌瀹炴椂鏁版嵁锛夈€?
- [backend/route/ctf_admin.py](backend/route/ctf_admin.py): 姣旇禌绠＄悊涓庣鐞嗗憳鎿嶄綔鎺ュ彛銆?
- [backend/route/admin.py](backend/route/admin.py): 骞冲彴绾х鐞嗘帴鍙ｃ€?
- [backend/route/articles.py](backend/route/articles.py): 鍏憡涓庢枃绔犵鐞嗐€?
- [backend/route/attachments.py](backend/route/attachments.py): 闄勪欢瀛樺彇鎺ュ彛銆?
- [backend/route/file_management.py](backend/route/file_management.py): 鏂囦欢绠＄悊宸ュ叿鎺ュ彛銆?
- [backend/route/games.py](backend/route/games.py): 涓庣珵璧?璧涘鐩稿叧鐨勬帴鍙ｃ€?
- [backend/route/competitions.py](backend/route/competitions.py): 绔炶禌閰嶇疆涓庡垪琛ㄣ€?
- [backend/route/challenge_admin.py](backend/route/challenge_admin.py): 棰樼洰绠＄悊锛堝垱寤?缂栬緫/瀵煎叆锛夈€?
- [backend/route/platform_admin.py](backend/route/platform_admin.py): 骞冲彴璁剧疆涓庣鐞嗗憳宸ュ叿銆?
- [backend/route/resources.py](backend/route/resources.py): 闈欐€佽祫婧愭垨澶栭儴璧勬簮浠ｇ悊銆?
- [backend/route/tokens.py](backend/route/tokens.py): Token/鍑瘉鐩稿叧鎺ュ彛銆?
- [backend/route/todos.py](backend/route/todos.py): 寰呭姙/浠诲姟鎺ュ彛锛堝唴閮ㄤ娇鐢級銆?

娉細涓婇潰閾炬帴鎸囧悜鍏蜂綋鏂囦欢锛屽悗缁彲閫愪釜鎻愬彇姣忎釜璺敱鍑芥暟鐨勫弬鏁般€佹潈闄愯姹備笌杩斿洖绀轰緥浠ヨˉ鍏ㄦ枃妗ｃ€?


---

## Source: docs\routes\admin.md

# 璺敱璇﹁В锛歚backend/route/admin.py`

鍔熻兘锛氬钩鍙扮骇绠＄悊鎺ュ彛锛屽寘鍚敤鎴风鐞嗐€佸璁℃棩蹇椼€佺郴缁熼厤缃瓑銆?

鍏抽敭绔偣锛堢ず渚嬶級锛?
- `GET /admin/users`锛氱敤鎴峰垪琛?
- `POST /admin/config`锛氱郴缁熼厤缃洿鏂?

娉ㄦ剰锛氭搷浣滄潈闄愪弗鏍硷紝浠呯鐞嗗憳鍙墽琛屻€?


---

## Source: docs\routes\articles.md

# 璺敱璇﹁В锛歚backend/route/articles.py`

鍔熻兘锛氬叕鍛娿€佹枃绔犱笌姣旇禌閫氱煡鐨勫垱寤恒€佺紪杈戙€佸彂甯冧笌鑾峰彇鎺ュ彛銆?

鍏抽敭绔偣锛?
- `GET /articles`锛氭枃绔犲垪琛?
- `POST /articles`锛氱鐞嗗憳鍙戝竷鍏憡


---

## Source: docs\routes\attachments.md

# 璺敱璇﹁В锛歚backend/route/attachments.py`

鍔熻兘锛氶檮浠朵笂浼犱笌绠＄悊锛岄€氬父閰嶅悎鏂囩珷/棰樼洰闄勫甫鏂囦欢鐨勪笂浼犱笌璁块棶鎺у埗銆?

鍏抽敭鐐癸細闄勪欢鍙瓨鍌ㄥ湪 `static/uploads/`锛屽簲鑰冭檻鏉冮檺涓庢湁鏁堟湡娓呯悊銆?


---

## Source: docs\routes\auth.md

# 璺敱璇﹁В锛歚backend/route/auth.py`

鍔熻兘锛氳璇佷笌浼氳瘽绠＄悊锛屽寘鍚敞鍐屻€佺櫥褰曘€佺櫥鍑恒€丣WT 鍒锋柊銆佸瘑鐮侀噸缃瓑鎺ュ彛銆?

鍏抽敭绔偣锛堢ず渚嬶級锛?
- `POST /auth/login`锛氱敤鎴风櫥褰曪紝杩斿洖 JWT銆?
- `POST /auth/register`锛氱敤鎴锋敞鍐屻€?
- `POST /auth/refresh`锛氬埛鏂拌闂护鐗岋紙闇€瑕?refresh token锛夈€?

閴存潈瑕佺偣锛氭晱鎰熸搷浣滆繑鍥炲拰瀵嗙爜澶勭悊閬靛惊瀹夊叏鏈€浣冲疄璺碉紙鍝堝笇銆侀€熺巼闄愬埗銆侀偖绠遍獙璇侊級銆?


---

## Source: docs\routes\challenge_admin.md

# 璺敱璇﹁В锛歚backend/route/challenge_admin.py`

鍔熻兘锛氶鐩紪鍐欎笌绠＄悊鎺ュ彛锛屾敮鎸侀鐩垱寤恒€佺紪杈戙€佸鍏ュ鍑轰笌娴嬭瘯鐢ㄤ緥绠＄悊銆?

鍏抽敭鐐癸細绠＄悊鍛樻帴鍙ｏ紝鍙兘鍖呭惈鏂囦欢涓婁紶锛堥檮浠?闄勪欢闀滃儚锛変笌棰樼洰楠岃瘉娴佺▼銆?


---

## Source: docs\routes\challenges.md

# 璺敱璇﹁В锛歚backend/route/challenges.py`

姒傝堪锛氭妯″潡瀹炵幇涓?CTF 棰樼洰鐩稿叧鐨勬墍鏈?API锛屽寘鍚鐩垪琛?璇︽儏銆佹彁浜?Flag銆佹帓琛屾銆佹彁绀虹郴缁熴€佷綔寮婃娴嬨€佸鍣ㄥ疄渚嬬鐞嗕笌棰樼洰缁熻绛夋牳蹇冨姛鑳姐€?

涓昏绔偣锛堟憳瑕侊級锛?

- `GET /games/<game_id>/challenges`
  - 閴存潈锛氬叕寮€
  - 鎻忚堪锛氳繑鍥炴寚瀹氱珵璧涚殑棰樼洰鍒楄〃锛堜粎鍚敤鐨勯鐩級銆?
  - 杩斿洖锛歿 code, msg, data: [challenge] }

- `GET /<challenge_id>`
  - 閴存潈锛歚@jwt_required()`
  - 鎻忚堪锛氳幏鍙栭鐩鎯呭苟闄勫甫褰撳墠鐢ㄦ埛鐨勬彁浜よ褰曚笌鏄惁宸茶В銆?
  - 杩斿洖锛歿 code, msg, data: { challenge, submissions, submission_count, is_solved } }

- `POST /<challenge_id>/submit`
  - 閴存潈锛歚@jwt_required()`
  - 鎻忚堪锛氭彁浜?Flag锛涘疄鐜板寘鎷瓟妗堟牎楠屻€佸姩鎬佸垎鏁拌绠椼€佽娑插鍔憋紙棣栬В/浜岃В/涓夎В锛夈€佷綔寮婃娴嬨€佹帓鍒嗘洿鏂般€佽禌瀛ｇ粺璁¤Е鍙戜笌瀹瑰櫒閿€姣侊紙姝ｇ‘鏃讹級銆?
  - 璇锋眰浣擄細{ answer: string }
  - 甯歌杩斿洖锛氭纭椂杩斿洖鏈€缁堝緱鍒嗐€佽娑茬瓑绾с€佸姞鎴愬€嶆暟锛涢敊璇椂杩斿洖鐩稿簲閿欒鐮佷笌娑堟伅銆?

- `GET /games/<game_id>/scoreboard`
  - 閴存潈锛氬叕寮€
  - 鎻忚堪锛氳幏鍙栨瘮璧涘疄鏃舵帓琛屾锛堢敱 `ScoringService.calculate_rankings` 璁＄畻锛夈€?

- `GET /games/<game_id>/first-solves`
  - 閴存潈锛氬叕寮€
  - 鎻忚堪锛氳幏鍙栭瑙?浜岃В/涓夎В璁板綍銆?

- `GET /<challenge_id>/hints`
  - 閴存潈锛歚@jwt_required()`
  - 鎻忚堪锛氳幏鍙栭鐩殑鎻愮ず鍒楄〃锛屽苟鏍囨敞褰撳墠鐢ㄦ埛宸茶闂殑鎻愮ず銆?

- `POST /<hint_id>/access-hint`
  - 閴存潈锛歚@jwt_required()`
  - 鎻忚堪锛氳褰曠敤鎴锋煡鐪嬫彁绀虹殑琛屼负锛涘鏋滄彁绀洪厤缃簡鎵ｅ垎锛屼細鏇存柊鎺掕姒滃垎鏁般€?

- `GET /games/<game_id>/cheat-info`
  - 閴存潈锛歚@jwt_required()`锛堥渶绠＄悊鍛樻潈闄愶級
  - 鎻忚堪锛氱鐞嗗憳鑾峰彇浣滃紛妫€娴嬩俊鎭紙`CtfCheatInfo` 璁板綍锛夈€?

- 瀹瑰櫒/瀹炰緥绠＄悊绔偣锛?
  - `GET /<challenge_id>/container-status`锛氭煡璇㈢敤鎴疯棰樼洰鐨勫鍣ㄧ姸鎬侊紙no_container/running/expired锛夈€?
  - `POST /<challenge_id>/start-container`锛氬惎鍔ㄩ鐩鍣紙闆嗘垚 `container_service.create_container` 涓庢祦閲忔崟鑾凤級銆?
  - `POST /<challenge_id>/start-instance`锛氫负鍔ㄦ€侀鐩垱寤哄疄渚嬭褰曪紙1灏忔椂鍒版湡锛屾敮鎸佹祦閲忔崟鑾凤級銆?
  - `POST /instances/<instance_id>/stop`锛氱敤鎴锋墜鍔ㄥ仠姝?閿€姣佸鍣ㄥ疄渚嬶紙鏉冮檺鏍￠獙锛夈€?
  - `POST /instances/<instance_id>/extend`锛氬欢鏃跺鍣ㄨ繃鏈熸椂闂达紙姣忔 +1 灏忔椂锛夈€?
  - `GET /instances/<instance_id>/status`锛氳幏鍙栧鍣ㄥ疄渚嬬姸鎬佷笌鍓╀綑鏃堕棿銆?

- `GET /<challenge_id>/stats`
  - 閴存潈锛氬叕寮€
  - 鎻忚堪锛氳繑鍥為鐩粺璁★紙鍞竴瑙ｉ浜烘暟銆佹€绘彁浜ゆ暟銆侀€氳繃鐜囥€侀瑙ｄ俊鎭級銆?

瀹炵幇瑕佺偣涓庢敞鎰忎簨椤癸細

- 鏉冮檺妫€鏌ワ細澶у鏁扮敤鎴锋搷浣滈渶瑕?`@jwt_required()`銆傜鐞嗗憳鎺ュ彛浼氳繘涓€姝ユ鏌?`user.is_admin`銆?
- 鎻愪氦闄愰€熶笌娆℃暟鎺у埗鐢遍鐩睘鎬э紙`submission_limit`锛変笌 `CtfChallengeSubmission` 璁℃暟瀹炵幇銆?
- 鍔ㄦ€佸垎鏁颁笌琛€娑插鍔辩敱 `ScoringService` 鎻愪緵锛屽叿浣撶畻娉曡 `backend/services/scoring_service.py`銆?
- 浣滃紛妫€娴嬭皟鐢?`CheatDetectionService.detect_similar_flags`锛屽鍙戠幇鐩镐技鎻愪氦浼氬啓鍏?`CtfCheatInfo`銆?
- 瀹瑰櫒鎿嶄綔渚濊禆鏈湴 Docker锛歚container_service` 鍦?`backend/services/container_service.py` 涓彁渚涘垱寤?閿€姣?鏌ヨ绛夋帴鍙ｏ紱鍚姩瀹瑰櫒鏃朵細鍦ㄥ悗鍙板惎鍔ㄦ祦閲忔崟鑾蜂唬鐞嗭紙鑻ュ惎鐢級锛屽苟鏇存柊瀹炰緥鐨?`connection_url`銆?
- 鏁版嵁搴撴ā鍨嬶紙濡?`CtfGameInstance`, `CtfChallengeSubmission` 绛夛級瀹氫箟鍦?`backend/server/db_models.py`锛屾枃妗ｄ腑寮曠敤浜?`.to_dict()` 鏂规硶鐢ㄤ簬搴忓垪鍖栧搷搴斻€?

寤鸿锛氬彲灏嗘湰鏂囦欢涓殑姣忎釜绔偣澶嶅埗鍒扮嫭绔嬬殑 Markdown 鏉＄洰涓紝琛ュ厖绀轰緥璇锋眰/鍝嶅簲涓庨敊璇爜琛紝渚夸簬鍓嶇鍜屾祴璇曚汉鍛樹娇鐢ㄣ€?


---

## Source: docs\routes\competitions.md

# 璺敱璇﹁В锛歚backend/route/competitions.py`

鍔熻兘锛氱珵璧涢泦鍚堜笌鍒嗙粍绠＄悊锛屾彁渚涚珵璧涚瓫閫夈€佹悳绱笌鎵归噺鎿嶄綔鎺ュ彛銆?


---

## Source: docs\routes\container_challenges.md

# 璺敱璇﹁В锛歚backend/route/container_challenges.py`

鍔熻兘锛氬鍣ㄥ寲棰樼洰鐨勪笓鐢ㄦ帴鍙ｏ紝閫氬父璐熻矗瀹瑰櫒闀滃儚銆佺綉缁滈殧绂汇€侀鐩疄渚嬬敓鍛藉懆鏈熺殑楂樼骇鎿嶄綔銆?

鍏抽敭绔偣锛堢ず渚嬶級锛?
- 鍚姩/鍋滄瀹瑰櫒瀹炰緥锛屾煡鐪嬪鍣ㄦ棩蹇?绔彛鏄犲皠锛岀鐞嗙綉缁滅瓥鐣ャ€?

瀹炵幇瑕佺偣锛氶厤鍚?`backend/services/container_service.py` 浣跨敤锛涙敞鎰?Docker 鏉冮檺涓庝富鏈鸿祫婧愰檺鍒躲€?


---

## Source: docs\routes\ctf_admin.md

# 璺敱璇﹁В锛歚backend/route/ctf_admin.py`

鍔熻兘锛氭瘮璧涚鐞嗘帴鍙ｏ紙绠＄悊鍛樻潈闄愶級锛屽寘鍚瘮璧涘垱寤恒€侀樁娈垫帶鍒躲€侀鐩壒閲忓鍏ヤ笌璧涚▼绠＄悊銆?

鍏抽敭鐐癸細浠呯鐞嗗憳鍙闂紱鎿嶄綔浼氳Е鍙?`scheduler` 涓?`season_stats_service` 鐨勭浉搴斾换鍔℃洿鏂般€?


---

## Source: docs\routes\ctf_api.md

# 璺敱璇﹁В锛歚backend/route/ctf_api.py`

鍔熻兘锛氶潰鍚戝墠绔殑姣旇禌瀹炴椂鏁版嵁鎺ュ彛锛岄€氬父鎻愪緵璧涘喌銆佹帓琛屾銆侀鐩眹鎬讳笌娲诲姩閫氱煡銆?

鍏抽敭绔偣锛?
- `GET /api/games/<id>/overview`锛氭瘮璧涙瑙堟暟鎹?
- `GET /api/games/<id>/live`锛氬疄鏃朵簨浠舵祦


---

## Source: docs\routes\file_management.md

# 璺敱璇﹁В锛歚backend/route/file_management.py`

鍔熻兘锛氭枃浠朵笌璧勬簮鐨勭鐞嗗伐鍏锋帴鍙ｏ紝鍖呭惈鎵归噺瀵煎叆/瀵煎嚭銆佸浠戒笌娓呯悊浠诲姟銆?

鍏抽敭鐐癸細閫氬父浠呯鐞嗗憳鍙闂紱娑夊強纾佺洏鎿嶄綔璇锋敞鎰忓苟鍙戜笌鏉冮檺銆?


---

## Source: docs\routes\games.md

# 璺敱璇﹁В锛歚backend/route/games.py`

鍔熻兘锛氱鐞嗘瘮璧?璧涘鐨勬帴鍙ｏ紝鍖呭惈姣旇禌鍒楄〃銆佽鎯呭強鍏冩暟鎹€?

绀轰緥绔偣锛歚GET /games`銆乣GET /games/<id>`銆乣POST /games`锛堢鐞嗗憳锛夈€?


---

## Source: docs\routes\platform_admin.md

# 璺敱璇﹁В锛歚backend/route/platform_admin.py`

鍔熻兘锛氬钩鍙拌缃€佺郴缁熺洃鎺с€佺鐞嗗憳宸ュ叿闆嗗悎锛堢敤鎴枫€侀槦浼嶃€佺郴缁熷弬鏁帮級銆?

浠呯鐞嗗憳鍙敤銆?


---

## Source: docs\routes\resources.md

# 璺敱璇﹁В锛歚backend/route/resources.py`

鍔熻兘锛氬閮ㄨ祫婧愭垨闈欐€佽祫婧愪唬鐞嗘帴鍙ｏ紝鍙兘鐢ㄤ簬绗笁鏂规湇鍔′唬鐞嗐€佸唴宓岃祫婧愯闂帶鍒躲€?


---

## Source: docs\routes\resources_overview.md

# 璧勬簮鎺ュ彛璇存槑

鏇村缁嗚妭璇锋煡鐪?`backend/route/resources.py`锛屽寘鎷閮?API 浠ｇ悊銆佸畨鍏ㄩ檺鍒朵笌缂撳瓨绛栫暐銆?


---

## Source: docs\routes\teams.md

# 璺敱璇﹁В锛歚backend/route/teams.py`

鍔熻兘锛氶槦浼嶅垱寤恒€佸姞鍏ャ€侀個璇枫€佹垚鍛樼鐞嗕笌闃熶紞閰嶇疆鎺ュ彛銆?

鍏抽敭绔偣锛堢ず渚嬶級锛?
- `POST /teams`锛氬垱寤洪槦浼?
- `POST /teams/<id>/invite`锛氶個璇锋垚鍛?
- `GET /teams/<id>`锛氳幏鍙栭槦浼嶄俊鎭笌鎴愬憳鍒楄〃

娉ㄦ剰鏉冮檺锛氬姞鍏?淇敼闃熶紞閫氬父闇€瑕侀獙璇佺敤鎴疯韩浠戒笌閭€璇风爜鏍￠獙銆?


---

## Source: docs\routes\teams_overview.md

# 璇存槑锛氬洟闃熸帴鍙ｅ揩閫熷弬鑰?

璇峰弬闃?`backend/route/teams.py` 鑾峰彇瀹屾暣瀹炵幇銆傛枃妗ｄ富瑕佽鐩栵細闃熶紞鐢熷懡鍛ㄦ湡銆侀個璇锋祦绋嬨€佹潈闄愯竟鐣屼笌甯歌閿欒鐮併€?


---

## Source: docs\routes\todos.md

# 璺敱璇﹁В锛歚backend/route/todos.py`

鍔熻兘锛氬唴閮ㄤ换鍔?寰呭姙椤圭洰鎺ュ彛锛岄€氬父鐢ㄤ簬杩愮淮鎴栧悗鍙颁换鍔℃帶鍒堕潰鏉裤€?


---

## Source: docs\routes\tokens.md

# 璺敱璇﹁В锛歚backend/route/tokens.py`

鍔熻兘锛歍oken/鍑瘉绠＄悊鎺ュ彛锛屽寘鍚敓鎴?楠岃瘉/鍚婇攢绛夋搷浣滐紙鐢ㄤ簬闃熶紞閭€璇风爜銆丄PI 璁块棶浠ょ墝绛夛級銆?


---

## Source: docs\routes\uploads.md

# 璺敱璇﹁В锛歚backend/route/uploads.py`

鍔熻兘锛氬鐞嗗墠绔笂浼犳枃浠躲€侀檮浠跺瓨鍌ㄣ€佽闂潈闄愪笌鏂囦欢娓呯悊銆?

鍏抽敭绔偣锛堢ず渚嬶級锛?
- `POST /uploads`锛氫笂浼犳枃浠讹紙琛ㄥ崟/澶氶儴鍒嗭級
- `GET /uploads/<id>`锛氫笅杞芥垨棰勮鏂囦欢

瀛樺偍娉ㄦ剰锛氭枃浠朵繚瀛樿矾寰勪负 `static/uploads/`锛屽簲闄愬埗涓婁紶澶у皬鍜岀被鍨嬫鏌ャ€?


---

## Source: docs\services\cheat_detection_service.md

# 鏈嶅姟璇﹁В锛歚backend/services/cheat_detection_service.py`

鑱岃矗锛氭娴嬮噸澶?鐩镐技鎻愪氦銆佸揩閫熸彁浜ゃ€両P 寮傚父锛岀敓鎴愪綔寮婃姤鍛婂苟鍐欏叆 `CtfCheatInfo`銆?

涓昏鏂规硶锛歚calculate_similarity`, `detect_duplicate_submission`, `detect_similar_submission`, `detect_rapid_submission`, `detect_ip_pattern`, `create_cheat_record`, `get_cheat_report`銆?

鎻愮ず锛氬彲鏍规嵁姣旇禌绛栫暐璋冩暣闃堝€硷紙鐩镐技搴︺€佹椂闂寸獥鍙ｇ瓑锛夈€?


---

## Source: docs\services\container_service.md

# 鏈嶅姟璇﹁В锛歚backend/services/container_service.py`

鑱岃矗锛氫笌 Docker 浜や簰锛屽垱寤?閿€姣佸鍣ㄣ€佹煡璇㈢姸鎬併€佽幏鍙栨棩蹇椼€佹竻鐞嗚繃鏈熷疄渚嬨€佺画鏈熺瓑銆?

涓昏鏂规硶锛歚create_container`, `destroy_container`, `get_container_status`, `cleanup_expired_containers`, `list_user_containers`, `renew_container_lease`, `get_container_logs`銆?

娉ㄦ剰锛氱敓浜х幆澧冮渶纭繚 Docker 鏉冮檺銆佸畨鍏ㄧ綉缁滀笌璧勬簮閰嶉锛涘缓璁 `create_container` 鍋氶檺娴佷笌閰嶉鏍￠獙銆?


---

## Source: docs\services\flag_generator.md

# 鏈嶅姟璇﹁В锛歚backend/services/flag_generator.py`

鑱岃矗锛氳В鏋?Flag 妯℃澘骞剁敓鎴愬姩鎬?Flag锛屾敮鎸?`[GUID]`, `[TEAM_HASH]`, `[LEET]`, `[CLEET]` 绛夊崰浣嶇涓?Leet 杞崲銆?

涓昏绫伙細`DynamicFlagGenerator`, `ContainerFlagService`銆?

绀轰緥锛氫娇鐢?`ContainerFlagService.generate_dynamic_flag(template, challenge_id, user_id, game_id)`銆?


---

## Source: docs\services\invite_code_service.md

# 鏈嶅姟璇﹁В锛歚backend/services/invite_code_service.py`

鑱岃矗锛氱敓鎴愩€佸垎鍙戜笌鏍￠獙閭€璇风爜锛岀敤浜庢帶鍒舵瘮璧涙垨闃熶紞鍔犲叆鏉冮檺銆?

鎺ュ彛閫氬父鍖呮嫭锛歚generate_code`, `validate_code`, `revoke_code`銆?


---

## Source: docs\services\permission_service.md

# 鏈嶅姟璇﹁В锛歚backend/services/permission_service.py`

鑱岃矗锛氭鏌ョ敤鎴峰湪姣旇禌/棰樼洰/闃熶紞涓婄殑鏉冮檺锛岄€氬父灏佽涓?`check_game_permission`, `has_submission_permission`, `has_container_permission` 绛夈€?

娉ㄦ剰锛氬疄闄呮潈闄愮粏鑺傚彲鑳藉垎鏁ｅ湪澶氫釜鏂囦欢锛坄scoring_service.py` 涓篃鍖呭惈 `PermissionService`锛夈€?


---

## Source: docs\services\redis_service.md

# 鏈嶅姟璇﹁В锛歚backend/services/redis_service.py`

鑱岃矗锛歊edis 杩炴帴绠＄悊銆佺紦瀛?API锛坓et/set/json锛夈€佹帓琛屾涓庨鐩紦瀛樸€侀€氱煡闃熷垪銆佺紦瀛樿楗板櫒 `cache_result`銆?

涓昏绫?鍑芥暟锛歚RedisService`, `ScoreboardCache`, `ChallengeCache`, `UserSessionCache`, `NotificationQueue`, `initialize_redis`銆?

娉ㄦ剰锛氶渶鏍规嵁鐜杩涜 `initialize_redis(host, port)`锛屽苟鍦ㄥ簲鐢ㄥ惎鍔ㄦ椂鍒涘缓鍏ㄥ眬瀹炰緥銆?


---

## Source: docs\services\scheduler.md

# 鏈嶅姟璇﹁В锛歚backend/services/scheduler.py`

鑱岃矗锛氬畾鏃朵换鍔′笌姣旇禌闃舵璋冨害锛屼緥濡傚紑濮?缁撴潫姣旇禌銆佹竻鐞嗚繃鏈熷鍣ㄣ€佺敓鎴愭棩甯告姤琛ㄧ瓑銆?

閫氬父涓庣郴缁?cron 鎴?`APScheduler` 闆嗘垚銆?


---

## Source: docs\services\scoring_service.md

# 鏈嶅姟璇﹁В锛歚backend/services/scoring_service.py`

涓昏绫讳笌鑱岃矗锛?
- `ScoringService`锛氬姩鎬佸垎鏁拌绠椼€佽娑插鍔便€佽褰曢瑙ｃ€佹洿鏂版帓琛屾銆佽绠楁帓鍚嶃€?
  - 鍏抽敭鏂规硶锛歚calculate_dynamic_score`, `calculate_blood_bonus`, `record_first_solve`, `update_scoreboard`, `calculate_rankings`銆?
- `CheatDetectionService`锛氳緟鍔╃殑浣滃紛妫€娴嬶紙瀛楃涓茬浉浼煎害銆佹娴嬬浉浼?Flags锛夈€?
- `FlagTemplateService`锛氭牴鎹ā鏉跨敓鎴愬姩鎬?Flag銆?
- `PermissionService` / `FlagValidationService`锛氭潈闄愪笌 Flag 楠岃瘉閫昏緫銆?

寤鸿锛氭帴鍙ｅ凡鍦?`backend/route/challenges.py` 琚绻佷娇鐢紱濡傞渶鍗曞厓娴嬭瘯锛屽彲閽堝 `calculate_dynamic_score` 鍜?`detect_similar_flags` 缂栧啓娴嬭瘯鐢ㄤ緥銆?


---

## Source: docs\services\season_stats_service.md

# 鏈嶅姟璇﹁В锛歚backend/services/season_stats_service.py`

鑱岃矗锛氳禌瀛ｇ粺璁¤仛鍚堜笌瑙﹀彂鍣紙濡傞鐩В鍐宠Е鍙戠粺璁℃洿鏂帮級銆?

甯歌鐢ㄩ€旓細鍦?`ScoringService` 鎴愬姛璁板綍瑙ｉ鍚庤皟鐢ㄤ互鏇存柊璧涘鎺掑悕涓庢眹鎬绘暟鎹€?


---

## Source: docs\faq.md

# 甯歌闂锛堝揩閫熷洖绛旓級

Q: 鎴戝浣曡繍琛岄」鐩紵

A: 鍚姩鍓嶇锛歚cd frontend && npm install && npm run dev`銆傚悗绔細鍙傞槄 `backend/app.py`锛岄€氬父浣跨敤铏氭嫙鐜杩愯 Python 绋嬪簭鎴栭€氳繃 ASGI/WSGI 鏈嶅姟鍣ㄨ繍琛屻€?

Q: 鎴戝浣曞畾浣嶆帴鍙ｅ疄鐜帮紵

A: 鍦?`backend/route/` 涓嬫寜妯″潡鏌ユ壘銆傝矾鐢遍€氬父浣跨敤妗嗘灦瑁呴グ鍣ㄦ敞鍐屻€?

Q: 娴嬭瘯濡備綍杩愯锛?

A: 杩愯 `pytest`锛堝浠撳簱鍖呭惈娴嬭瘯鏂囦欢锛夈€?

Q: 鎹曡幏鏂囦欢锛圥CAP锛夊湪鍝紵

A: 鍦?`captures/` 鐩綍涓嬶紝鎸夋寫鎴樹笌闃熶紞缂栧彿鍒嗙被銆?

Q: 鎴戞兂鎵╁睍鏈嶅姟鎴栨柊澧炶矾鐢憋紝鍦ㄥ摢閲屾敞鍐岋紵

A: 鍦?`backend/server/` 涓嬫煡鎵炬墿灞曟敞鍐岀偣锛坄extensions.py` 鎴?`app.py`锛夈€?


---


