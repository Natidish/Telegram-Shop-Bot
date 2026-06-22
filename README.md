# Multi-Tenant Telegram Shop Bot — Setup መመሪያ

ይህ ቦት **ብዙ ነጋዴዎች በ1 ቦት** እንዲጠቀሙ የተዘጋጀ ነው። እያንዳንዱ ነጋዴ `/register` ብሎ የራሱን ስቶር ይከፍታል እና የራሱ unique link ያገኛል። ደንበኞች ያንኑ link ሲጫኑ ቀጥታ ወደ እርሱ ስቶር menu ይገባሉ።

## ፋይሎች
- `bot.py` — ሁሉም bot logic (registration, order, menu...)
- `storage.py` — stores.json / orders.json ላይ የሚፅፍ/የሚያነብ ቀላል data layer
- `requirements.txt` — dependencies

---

## 1. Bot Token ማግኘት
1. Telegram ላይ **@BotFather** ን ያናግሩ
2. `/newbot` ይላኩ
3. የሚሰጥዎትን **token** ይቅዱ

ይህ ቦት ለ*ብዙ ነጋዴዎች* ስለሆነ **OWNER_CHAT_ID አያስፈልግም** — እያንዳንዱ ነጋዴ ሲመዘገብ የራሱ Telegram ID በራስ-ሰር ይያያዛል።

---

## 2. Render ላይ Deploy ማድረግ (Free Web Service)

ይህ ቦት **webhook mode** ይጠቀማል (ፓysorт polling ሳይሆን) ስለዚህ Render free **Web Service** ላይ በትክክል ይሰራል (Background Worker ክፍያ ስለሚጠይቅ አያስፈልግም)።

### Render Dashboard ላይ:
| Setting | Value |
|---|---|
| Service Type | **Web Service** |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python bot.py` |
| Environment Variable | `BOT_TOKEN` = የራስዎ token |

**`RENDER_EXTERNAL_URL` ን እጅ መንካት አያስፈልግም** — Render ራሱ ለ Web Service በራስ-ሰር ይፈጥረዋል፣ ኮዱም ራሱ ይህን አውቆ ወደ webhook mode ይቀየራል።

### Deploy ካደረጉ በኋላ
Render ሎግ ላይ ይህን ካዩ ስራ ላይ ነው፡
```
🌐 Webhook mode ላይ በ Render እየጀመረ ነው → https://your-app.onrender.com
```

### ⚠️ አንድ ጠንቃቃ ነጥብ — Free Tier "Spin Down"
Render free Web Service ለ15 ደቂቃ ምንም ጥቅም ካላገኘ "ይተኛል" (spin down)፣ ቀጥሎ የሚመጣ ጥያቄ ሲደርሰው ለ30-60 ሰከንድ ያህል ዘግይቶ ይነሳል (cold start)። ይህ ለ pilot/ሙከራ ደረጅ ችግር አይፈጥርም፣ ነገር ግን ለነጋዴ ጥሩ ልምድ እንዲሰጥ ከፈለጉ፡
- **UptimeRobot** (ነፃ) በመጠቀም ቦቱን በየ10 ደቂቃ ping ቢያደርጉት ሁል ጊዜ "ነቅቶ" ይቆያል (750 free hours/month ስላለ ለ1 service ያስኪደው ይበቃል)
- ወይም ለቁም ነገር ስራ ላይ ሲደርሱ Render's paid tier ($7/month) ላይ መሄድ - cold start ሙሉ በሙሉ ያስቀራል

---

## 3. Local ላይ ሙከራ

```bash
pip install -r requirements.txt
export BOT_TOKEN="የራስዎ_token"
python bot.py
```

`RENDER_EXTERNAL_URL` ስለሌለ ኮዱ ራሱ ወደ **polling mode** ይቀየራል — local ሙከራ ላይ webhook ማዋቀር አያስፈልግም።

---

## 4. ነጋዴ እንዴት ይጠቀማል (Onboarding Flow)

| Command | ምን ያደርጋል |
|---|---|
| `/register` | አዲስ ስቶር መክፈት (ስም → ስልክ → ቦታ → ምርቶች) |
| `/mystore` | የስቶር መረጃ + የራስዎ unique customer link ማየት |
| `/addproduct` | ተጨማሪ ምርት መጨመር |
| `/removeproduct` | ምርት ማስወገድ |
| `/myorders` | የቅርብ ጊዜ ትዕዛዞችን ማየት |

ምሳሌ ሂደት፡
1. ነጋዴ ቦቱን ያገኛል → `/register` → ስም/ስልክ/ቦታ/ምርቶች ይሞላል
2. ቦቱ ይህን ይመልሳል፡ `https://t.me/YourBot?start=store_123456789`
3. ነጋዴው ይህን link በ Telegram channel/Facebook ላይ ያጋራል
4. ደንበኛ link ይጫናል → ቀጥታ የእርሱን ስቶር menu ያያል → ያዛል
5. ትዕዛዙ ለነጋዴው ስልክ/Telegram ላይ notification ይደርሰዋል

---

## 5. Data የት ይቀመጣል?

`stores.json` እና `orders.json` በራስ-ሰር ይፈጠራሉ። **ጠንቃቃ ይሁኑ፡** Render free Web Service እንደገና deploy ሲደረግ (ለምሳሌ ኮድ ቀይረው ሲገፉ) disk-ላይ ያሉ ፋይሎች ሊጠፉ ይችላሉ (ephemeral filesystem)። ለ pilot ደረጅ ችግር የለውም፣ ለ production ግን፡
- Render's **Persistent Disk** ($ ይከፈላል) መጠቀም፣ ወይም
- ወደ real database (PostgreSQL — Render free tier 30 ቀን ነፃ አለው) መቀየር ይመከራል

ይህን ክፍል ስትደርስ ንገረኝ — የ database migration ኮድ ላዘጋጅልህ።

---

## 6. ቀጣይ ሊጨመሩ የሚችሉ ፊቸሮች
- 💳 Chapa payment integration (ትዕዛዝ ላይ ቀጥታ ክፍያ)
- 📊 ለነጋዴ ቀላል dashboard (web ላይ ሽያጭ ቁጥር ለማየት)
- 🔔 Broadcast — ነጋዴ ለሁሉም ደንበኞቹ በቀጥታ ማስታወቂያ መላክ
