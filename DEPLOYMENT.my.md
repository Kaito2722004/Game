# အွန်လိုင်းတင်ခြင်း လမ်းညွှန်

> English version: [DEPLOYMENT.md](DEPLOYMENT.md)

အပိုင်း ၃ ပိုင်း၊ ဝဘ်ဆိုက် ၃ ခု၊ အားလုံး အခမဲ့ —

```
  Browser (ကြည့်သူ)
       │
       ▼
   Vercel ────────► Render ────────► Neon
   React app       FastAPI API     PostgreSQL
   (မျက်နှာပြင်)     (တွက်ချက်မှု)      (ဒေတာသိမ်း)
```

**အစဉ်လိုက် လုပ်ရပါမယ်။** တစ်ဆင့်ချင်းစီက အရင်တစ်ဆင့်ရဲ့ URL ဒါမှမဟုတ်
connection string ကို လိုအပ်လို့ပါ။

---

## မစခင် ပြင်ဆင်ရန်

ဝဘ်ဆိုက် ၃ ခုမှာ အကောင့်ဖွင့်ရပါမယ်။ သုံးခုလုံးကို **GitHub နဲ့ sign up**
လုပ်ရင် နှစ်မိနစ်လောက်ပဲ ကြာပါတယ် —

- <https://neon.tech> — database
- <https://render.com> — backend
- <https://vercel.com> — frontend

**Notepad တစ်ခုဖွင့်ထားပါ။** တန်ဖိုး ၃ ခု စုဆောင်းရမှာဖြစ်ပါတယ် —

| တန်ဖိုး | ဘယ်ကရမလဲ | ပုံစံ |
|---|---|---|
| Database URL | Neon | `postgresql://user:pass@ep-xxx.neon.tech/db` |
| API URL | Render | `https://prisoners-dilemma-api.onrender.com` |
| Frontend URL | Vercel | `https://your-project.vercel.app` |

---

## အဆင့် ၁ — Database (Neon)

၁။ Project အသစ်တစ်ခု ဖန်တီးပါ။ နာမည်က ဘာမဆိုရပါတယ်။ Region ကတော့
   အနီးဆုံးကို ရွေးပါ (Singapore)။

၂။ **Connection Details** ကိုဖွင့်ပြီး connection string ကို copy ကူးပါ။

၃။ **အဲဒီ string ကို နည်းနည်းပြင်ရပါမယ်။** Neon က `postgresql://` လို့ပေးပါတယ်။
   ဒါပေမဲ့ ဒီ project က driver နာမည်နဲ့ SSL လိုအပ်ပါတယ် —

   ```
   postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
   ```

   **ပြင်ရမှာ နှစ်နေရာပဲ —**
   - `postgresql://` → `postgresql+psycopg://` ပြောင်း
   - နောက်ဆုံးမှာ `?sslmode=require` ထည့် (မပါသေးရင်)

ဒီအဆင့်မှာ တခြားဘာမှလုပ်စရာမလိုပါဘူး။ Table တွေက အဆင့် ၂ မှာ
အလိုအလျောက် ဖန်တီးပါလိမ့်မယ်။

---

## အဆင့် ၂ — Backend (Render)

၁။ **New → Web Service** နှိပ်ပြီး GitHub repository ကို ချိတ်ပါ။
   Branch — `main` ရွေးပါ။

၂။ Render က [`render.yaml`](render.yaml) ကို ဖတ်ပါတယ်။ ဒါကြောင့် build နဲ့
   start command တွေ အလိုအလျောက် ဖြည့်ပြီးသားပါ။ **မထိပါနဲ့။**

၃။ Environment variable တွေ ဖြည့်ပါ —

   | Variable | တန်ဖိုး |
   |---|---|
   | `DATABASE_URL` | အဆင့် ၁ က ပြင်ထားတဲ့ Neon string |
   | `FIRST_ADMIN_EMAIL` | သင့် email |
   | `FIRST_ADMIN_PASSWORD` | **သင်ကိုယ်တိုင်ရွေးတဲ့ password အစစ်** |
   | `CORS_ORIGINS` | ခုတော့ ဗလာထားပါ (အဆင့် ၄ မှာ ဖြည့်မယ်) |

   `SECRET_KEY` ကို Render က အလိုအလျောက် ထုတ်ပေးပါတယ်။ **သင်မဖြည့်ပါနဲ့။**

၄။ Deploy နှိပ်ပါ။ ပထမဆုံးအကြိမ် မိနစ်အနည်းငယ် ကြာပါတယ်။ စတင်တဲ့အခါ
   migration နဲ့ seed ကို အလိုအလျောက် run ပေးလို့ table တွေ၊ မဟာဗျူဟာ ၆ ခု၊
   default payoff matrix နဲ့ သင့် admin account အားလုံး ပေါ်လာပါလိမ့်မယ်။

၅။ စစ်ကြည့်ပါ — `https://YOUR-API.onrender.com/docs` ကိုဖွင့်ပါ။
   Swagger စာမျက်နှာ ပေါ်ရပါမယ်။

> ### ⚠️ အရေးကြီးသော လုံခြုံရေး
>
> `SECRET_KEY` က default အတိုင်းဖြစ်နေရင် ဒါမှမဟုတ် `CORS_ORIGINS` ဗလာဖြစ်နေရင်
> **app က စတင်မှာမဟုတ်ပါဘူး**။ Default admin password နဲ့လည်း admin account
> ဖန်တီးမှာ မဟုတ်ပါဘူး။
>
> အကြောင်းရင်းက — အဲဒီတန်ဖိုးတွေဟာ ဒီ GitHub repository ထဲမှာ **အများမြင်နိုင်တဲ့
> အနေအထား** ဖြစ်နေလို့ပါ။ အဲဒါတွေအတိုင်း အွန်လိုင်းတင်လိုက်ရင် code ကိုဖတ်တတ်တဲ့
> ဘယ်သူမဆို သင့် admin account ထဲ ဝင်လို့ရသွားပါလိမ့်မယ်။
>
> Deploy မအောင်မြင်ရင် log ကိုဖတ်ပါ — ဘာလိုနေလဲ အတိအကျ ပြောပြပါလိမ့်မယ်။

---

## အဆင့် ၃ — Frontend (Vercel)

၁။ **Add New → Project** နှိပ်ပြီး အလားတူ repository ကို import လုပ်ပါ။

၂။ **Root Directory ကို `frontend` လို့ သတ်မှတ်ပါ။**
   ⚠️ ဒါက အများဆုံး မေ့တတ်တဲ့အဆင့်ပါ။ မသတ်မှတ်ရင် Vercel က repository
   အပြင်ဘက်မှာ `package.json` ရှာပြီး build မအောင်မြင်ပါဘူး။

၃။ Framework preset — **Vite**။ ကျန်တာတွေက
   [`frontend/vercel.json`](frontend/vercel.json) ထဲကနေ အလိုအလျောက် ရပါတယ်။

၄။ Environment variable တစ်ခု ထည့်ပါ —

   | Variable | တန်ဖိုး |
   |---|---|
   | `VITE_API_BASE_URL` | `https://YOUR-API.onrender.com/api/v1` |

   ⚠️ နောက်ဆုံးက **`/api/v1` က မဖြစ်မနေလိုပါတယ်**။ မပါရင် request တိုင်း
   404 error တက်ပါလိမ့်မယ်။

၅။ Deploy နှိပ်ပြီး ရလာတဲ့ URL ကို မှတ်ထားပါ။

---

## အဆင့် ၄ — နှစ်ခုကို မိတ်ဆက်ပေးခြင်း

Render ကို ပြန်သွားပြီး `CORS_ORIGINS` မှာ Vercel URL ကို ဖြည့်ပါ —

```
CORS_ORIGINS=https://your-project.vercel.app
```

နောက်ဆုံးမှာ `/` မထည့်ပါနဲ့။ Render က အလိုအလျောက် restart လုပ်ပါလိမ့်မယ်။

ဒါကို မလုပ်ရင် — API က ကောင်းကောင်းအလုပ်လုပ်နေပေမဲ့ browser က request
တွေကို ပိတ်ဆို့ထားလို့ frontend မှာ **"Unable to connect to the backend"**
လို့ပဲ ပေါ်နေပါလိမ့်မယ်။

---

## အဆင့် ၅ — အစအဆုံး စစ်ဆေးခြင်း

Vercel URL ကိုဖွင့်ပြီး အောက်ပါတို့ကို စစ်ပါ —

- [ ] Sign in စာမျက်နှာ ပေါ်လာသလား
- [ ] သင့် admin email နဲ့ password နဲ့ ဝင်လို့ရသလား
- [ ] **Strategies** မှာ မဟာဗျူဟာ ၆ ခု ပေါ်သလား
      → API နဲ့ database ချိတ်မိကြောင်း သက်သေ
- [ ] **Payoff Matrix** မှာ DD ကွက်ပေါ်မှာ Nash badge ပေါ်သလား
      → တွက်ချက်မှု engine အလုပ်လုပ်ကြောင်း သက်သေ
- [ ] Tournament ဖန်တီးပြီး run လုပ်ရင် အဆင့်ဇယား ထွက်လာသလား
- [ ] `/history` လို link ကို refresh လုပ်ရင် 404 မတက်ဘဲ ပုံမှန်ပေါ်သလား

---

## သိထားသင့်တဲ့ အချက်များ

### ၁။ Render အခမဲ့ဟာ အိပ်ပျော်သွားတတ်ပါတယ် ⚠️

မိနစ် ၁၅ ကြာ ဘယ်သူမှမသုံးရင် server က ရပ်သွားပါတယ်။ နောက်တစ်ခါ ဝင်ကြည့်တဲ့အခါ
**စက္ကန့် ၅၀ လောက် စောင့်ရ**ပါတယ်။ အဲဒီအချိန်မှာ frontend က
"backend unreachable" လို့ပြနေပါလိမ့်မယ်။

> **သရုပ်ပြပွဲအတွက် — မတင်ပြခင် ၅ မိနစ်အလိုမှာ API URL ကို ဖွင့်ထားပါ။**
> ဒါက ဆရာရှေ့မှာ အမှားဖြစ်နိုင်ခြေ အများဆုံးအချက်ပါ။

### ၂။ Database နှစ်ခု သီးခြားဖြစ်နေပါတယ်

သင့် laptop မှာ local PostgreSQL ရှိပါတယ်။ အွန်လိုင်းဆိုက်က Neon ကိုသုံးပါတယ်။
**ဒေတာတွေ တစ်ခုနဲ့တစ်ခု မကူးပါဘူး** — laptop မှာ run ထားတဲ့ tournament က
အွန်လိုင်းမှာ ပေါ်မှာမဟုတ်ပါဘူး၊ ပြောင်းပြန်လည်း အတူတူပါပဲ။

သင် အခုမှတ်တမ်းတင်ထားပြီးသား classroom experiment ကလည်း laptop မှာပဲ
ကျန်ရစ်ပါလိမ့်မယ်။

### ၃။ ဝင်ကြည့်သူတိုင်း database တစ်ခုတည်းကို မျှသုံးပါတယ်

Link ရှိတဲ့ ဘယ်သူမဆို ဒေတာကို ဖတ်လို့ရပါတယ်။ Login ဝင်နိုင်တဲ့သူဆိုရင်
ဒေတာထပ်ထည့်လို့လည်း ရပါတယ်။ ကျောင်းပရောဂျက်အတွက် ပြဿနာမရှိပေမဲ့
သိထားသင့်ပါတယ်။

### ၄။ Tournament အကြီးကြီးများ

မဟာဗျူဟာ ၆ ခု × အပတ် ၁၀၀ = စက္ကန့် ၀.၀၄ လောက်ပဲ ကြာလို့ အခမဲ့ tier နဲ့
လုံလောက်ပါတယ်။ ဒါပေမဲ့ `repetitions` အရမ်းများရင် timeout ဖြစ်နိုင်ပါတယ်။
အဲဒီအခါ **rounds ကိုမလျှော့ဘဲ repetitions ကို လျှော့ပါ**။

---

## အွန်လိုင်းတင်ပြီးနောက် laptop မှာ ဆက်သုံးခြင်း

ဘာမှမပြောင်းလဲပါဘူး။ `.env` ဖိုင်က gitignore ထဲမှာရှိလို့ GitHub ကို
မတက်ပါဘူး၊ သင့် local PostgreSQL ကိုပဲ ညွှန်နေဆဲပါ။ Command နှစ်ခုက
အတူတူပါပဲ —

```bash
uvicorn app.main:app --reload
```

```bash
npm run dev --prefix frontend
```

---

## ပြဿနာတက်ရင်

| မြင်ရတဲ့ပြဿနာ | အကြောင်းရင်း | ဖြေရှင်းနည်း |
|---|---|---|
| Vercel build မအောင်မြင် | Root Directory မသတ်မှတ်ထား | Settings မှာ `frontend` လို့ ထည့် |
| "Unable to connect to the backend" | `CORS_ORIGINS` မဖြည့်ရသေး | အဆင့် ၄ လုပ်ပါ |
| Request တိုင်း 404 | `VITE_API_BASE_URL` မှာ `/api/v1` မပါ | နောက်ဆုံးမှာ ထည့်ပါ |
| Render deploy fail — SECRET_KEY | Default အတိုင်းဖြစ်နေ | Render က အလိုအလျောက်ထုတ်ပေးတာကို သုံးပါ |
| Render deploy fail — password | `FIRST_ADMIN_PASSWORD` မဖြည့်ရသေး | Password အစစ်တစ်ခု ဖြည့်ပါ |
| Database ချိတ်လို့မရ | `postgresql+psycopg://` မပြောင်းရသေး | အဆင့် ၁ အပိုဒ် ၃ ပြန်ကြည့်ပါ |
| ပထမဆုံး ဝင်ကြည့်တာ အရမ်းနှေး | Render အိပ်ပျော်နေ | စက္ကန့် ၅၀ စောင့်ပါ (ပုံမှန်ပါ) |
