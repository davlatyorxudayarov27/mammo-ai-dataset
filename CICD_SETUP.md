# CI/CD sozlash — push qilsang server o'zi yangilanadi

**Maqsad:** lokal va server hech qachon ajralmasin. Yagona haqiqat manbasi —
**GitHub**. Hamma o'zgarish: lokalда tahrirlash → `git push` → server **avtomatik**
`git pull` + `docker compose` rebuild qiladi.

> ⛔ Bundan keyin **serverда fayllarni QO'LDA tahrirlamang**. Aks holda yana ajraladi.

Arxitektura: 10.10.0.75 ichki IP — GitHub bulutli runnerlari unga ulanolmaydi,
shuning uchun **serverда "self-hosted runner"** ishlaydi. Push bo'lishi bilan
GitHub serverдаги runnerга ishorat beradi, u esa o'zида (10.10.0.75) deploy qiladi.

---

## 1-qadam — Serverни GitHub bilan bir xil qilish (bir martalik)

Serverда (`ssh ai@10.10.0.75`):

```bash
cd /home/ai/plan_project_new

# Git repo'mi tekshiring:
git rev-parse --is-inside-work-tree 2>/dev/null && echo "GIT BOR" || echo "GIT YO'Q"
```

**Agar "GIT YO'Q" bo'lsa** (tar.gz bilan ko'chirilgan, git ulanmagan):
```bash
git init
git remote add origin https://github.com/davlatyorxudayarov27/mammo-ai-dataset.git
git fetch origin
git reset --hard origin/feature/multilabel-radiomics-ensemble
git checkout -B feature/multilabel-radiomics-ensemble --track origin/feature/multilabel-radiomics-ensemble
```

**Agar "GIT BOR" bo'lsa:**
```bash
git status            # serverдаги qo'lda o'zgarishlarni ko'ring
git fetch origin
git reset --hard origin/feature/multilabel-radiomics-ensemble
```

> ✅ Xavfsiz: `uploads/`, `annotations/`, `db.sqlite3`, `models/`, `.env` —
> `.gitignore`да yoki Docker volume'larда, shuning uchun `reset --hard` ularга
> tegmaydi. Faqat **kod** GitHub bilan bir xil bo'ladi.
> ⚠️ Agar serverда saqlash kerak bo'lgan kod o'zgarishi bo'lsa — avval
> `git stash` qiling yoki menga ayting.

### Private repo bo'lsa — git auth
Repo private bo'lsa, server `git fetch` uchun kalit kerak. Eng oson — **deploy key**:
```bash
ssh-keygen -t ed25519 -C "mamograf-server" -f ~/.ssh/mamograf_deploy -N ""
cat ~/.ssh/mamograf_deploy.pub
# Bu kalitni GitHub'ga qo'shing: repo → Settings → Deploy keys → Add deploy key (Read-only yetarli)
git remote set-url origin git@github.com:davlatyorxudayarov27/mammo-ai-dataset.git
# SSH config (deploy key ishlatish uchun):
printf 'Host github.com\n  IdentityFile ~/.ssh/mamograf_deploy\n  IdentitiesOnly yes\n' >> ~/.ssh/config
git fetch origin && echo "auth OK"
```
> Repo public bo'lsa bu qadam kerak emas.

---

## 2-qadam — Self-hosted runner o'rnatish (bir martalik)

GitHub'да: **repo → Settings → Actions → Runners → New self-hosted runner →
Linux**. U yerda ko'rsatilgan buyruqlarni nusxalang (ular TOKEN bilan keladi),
faqat `./config.sh` qatoriga **`--labels mamograf`** qo'shing:

```bash
# Serverда:
mkdir -p ~/actions-runner && cd ~/actions-runner
# (GitHub UI'dagi aniq versiya/URL'ni ishlating — quyidagi namuna)
curl -o runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.319.1/actions-runner-linux-x64-2.319.1.tar.gz
tar xzf runner.tar.gz

# GitHub UI bergan TOKEN bilan (token ~1 soat amal qiladi):
./config.sh --url https://github.com/davlatyorxudayarov27/mammo-ai-dataset \
            --token <GITHUB_BERGAN_TOKEN> \
            --name mamograf-server \
            --labels mamograf \
            --unattended

# Xizmat sifatida o'rnatib, doim ishlab tursin (server qayta yuklansa ham):
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status      # "active (running)" bo'lsin
```

GitHub'да **Settings → Actions → Runners**'да `mamograf-server` — **Idle** (yashil)
ko'rinishi kerak.

---

## 3-qadam — Runner Docker'ни ishlata olsin

Runner qaysi foydalanuvchi nomidan ishlasa (odatda `ai`), u `docker` guruhида
bo'lsin:
```bash
sudo usermod -aG docker ai
sudo ./svc.sh stop && sudo ./svc.sh start    # guruh yangilanishi uchun
docker ps    # xatosiz ishlasa — tayyor
```

---

## 4-qadam — Ishlatish (bundan keyin shu)

Lokalда:
```bash
# kod tahrirlaysiz ...
git add -A
git commit -m "o'zgarish tavsifi"
git push origin feature/multilabel-radiomics-ensemble
```
Push bo'lishi bilan GitHub Actions → serverдаги runner → avtomatik
`git pull` + `docker compose up -d --build` qiladi. **Tamom.**

Borishini kuzatish: GitHub → **Actions** tab → "Deploy (prod)" workflow.
Qo'lda ishga tushirish: Actions → Deploy (prod) → **Run workflow**.

---

## Tekshirish va troubleshooting

| Holat | Tekshirish / yechim |
|---|---|
| Runner ko'rinmayapti | `sudo ~/actions-runner/svc.sh status`; GitHub Runners sahifasi |
| Deploy "queued" bo'lib qoladi | runner offline yoki `mamograf` label mos emas |
| `docker: permission denied` | 3-qadam (docker guruh) bajarilmagan |
| `git fetch` auth xato | private repo → deploy key (1-qadam) |
| Deploy logи | GitHub → Actions → oxirgi run → "Git pull + Docker rebuild" |
| Tekshirish | `curl -s http://localhost:8081/ \| head -c 120` (yoki prod port) |

---

## Muhim qoidalar (ajralmaslik uchun)
1. **Serverда kod QO'LDA tahrirlanmaydi** — faqat git orqali keladi.
2. Yagona deploy shoxchasi: `feature/multilabel-radiomics-ensemble`
   (kelajakда `main`ga birlashtirish toza bo'ladi — ixtiyoriy).
3. Ma'lumot (`uploads/db/models`) Docker volume'larда — deploy ularга tegmaydi.
4. Backup avtomatik emas — `db`/`annotations` volume'larни vaqti-vaqti bilan
   zaxiralang (DEPLOY.md §4).
