# Aksoy Hukuk Bürosu — Otomatik Yargıtay Kararı Paylaşımı

Haftada 4 gün (Pzt, Sal, Per, Cum, saat 10:00) kuyruktaki sıradaki **onaylı** kararı
altın sarısı kart görseliyle **Instagram, X ve LinkedIn**'de paylaşır. Sistem GitHub
Actions üzerinde ücretsiz çalışır; bilgisayarınızın açık olması gerekmez.

```
kararlar/001-....yaml   ← siz kararı yazarsınız, kontrol edip "onay: true" yaparsınız
        │
        ▼  (Pzt/Sal/Per/Cum 10:00, otomatik)
paylas.py → kart görseli (1080x1350) + platforma özel metin
        │
        ├─ Instagram  (görsel + uzun açıklama + 30'a kadar hashtag)
        ├─ X          (280 karaktere sığdırılmış, bağlantısız)
        └─ LinkedIn   (şirket sayfası veya kişisel profil)
        │
        ▼
kararlar/paylasilanlar/  +  gecmis.json  (hangi karar nerede, ne zaman paylaşıldı)
```

## 1. Günlük kullanım

1. `kararlar/` klasörüne her karar için bir dosya ekleyin (`001-ornek-kidem-tazminati.yaml`
   örneğini kopyalayın). Dosyalar ad sırasına göre paylaşılır: `002-...`, `003-...`
2. Metni kontrol edin ve `onay: true` yapın. Onaysız kararlar **asla** paylaşılmaz.
3. Bu kadar. Haftada 4 paylaşım için ayda ~17 onaylı karar yeterlidir.

Kuyrukta onaylı karar kalmazsa çalışma "başarısız" görünür ve GitHub size e-posta atar;
böylece içerik bittiğini hemen öğrenirsiniz. Bir platform hata verirse diğerleri yine
paylaşılır, hatalı olan bir sonraki çalışmada yeniden denenir.

**Önizleme (yayınlamadan bakmak için), bilgisayarınızda:**
```bash
pip install -r requirements.txt
python paylas.py --onizleme --dosya 002-....yaml   # onizleme/ klasörüne görsel + metinler
python paylas.py --kuyruk                           # kaç onaylı karar kaldı?
```

**İsteğe bağlı — yapay zekâ taslağı:** Karar metnini karararama.yargitay.gov.tr'den
kopyalayıp `ham/` klasörüne `.txt` olarak yükleyin. `taslak.yml` iş akışı Claude ile
`onay: false` taslak YAML üretir. Siz okuyup düzeltip onaylarsınız. (`ANTHROPIC_API_KEY`
gizli anahtarı gerekir; console.anthropic.com.)

## 2. Bir kerelik kurulum

### 2.1 GitHub deposu
1. github.com'da hesap açın → **New repository** → ad: `aksoy-paylasim`.
   - Görselleri GitHub'dan sunacaksanız (varsayılan) depo **Public** olmalı.
     Taslakların görünmesini istemiyorsanız depoyu **Private** yapın ve
     `config.yaml` içinde `gorsel_barindirma: "imgbb"` seçin (imgbb.com → ücretsiz API anahtarı
     → `IMGBB_API_KEY`).
2. Bu klasördeki tüm dosyaları depoya yükleyin (*Add file → Upload files*; `.github`
   klasörü dahil).
3. **Settings → Secrets and variables → Actions → New repository secret** ile aşağıdaki
   anahtarları ekleyin.

### 2.2 Instagram (Meta Graph API)
Ön şart: Instagram hesabı **İşletme/Profesyonel** olmalı ve bir **Facebook Sayfasına bağlı** olmalı.
1. developers.facebook.com → **Uygulama oluştur** → tür: *Business*.
2. Ürün olarak **Instagram** ekleyin; izinler: `instagram_basic`, `instagram_content_publish`,
   `pages_show_list`.
3. Kalıcı anahtar için en sağlam yol: business.facebook.com → *Ayarlar → Sistem Kullanıcıları*
   → sistem kullanıcısı oluşturun, uygulamayı ve sayfayı atayın → **süresiz token** üretin.
   (Normal kullanıcı tokenları 60 günde biter.)
4. Graph API Explorer'da `me/accounts?fields=instagram_business_account` sorgusuyla
   Instagram hesap ID'nizi bulun.
5. Gizli anahtarlar: `IG_USER_ID`, `IG_ACCESS_TOKEN`

### 2.3 X (Twitter)
1. console.x.com (developer.x.com) → proje + uygulama oluşturun.
2. *User authentication settings* → izin: **Read and write**.
3. *Keys and tokens* → API Key/Secret ve **Access Token/Secret** üretin (izni değiştirdikten
   SONRA üretin, yoksa token salt-okunur kalır).
4. Faturalandırmaya kredi yükleyin. X 2026'dan beri kullandıkça öde modelinde: bağlantısız
   gönderi ≈ 0,015 $ → ayda ~17 gönderi ≈ **0,26 $**. Kod bilerek bağlantı eklemez
   (bağlantılı gönderi ≈ 0,20 $).
5. Gizli anahtarlar: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET`

### 2.4 LinkedIn
**Şirket sayfası** (`yazar_turu: "organization"`):
1. linkedin.com/developers → uygulama oluşturun, şirket sayfanızla ilişkilendirin.
2. **Community Management API** ürününe başvurun (LinkedIn onayı gerekir; birkaç gün-hafta
   sürebilir). İzin: `w_organization_social`. Sayfada **Yönetici** rolünüz olmalı.
3. `LINKEDIN_AUTHOR_URN` = `urn:li:organization:<sayfa numarası>` (sayfa yönetici
   panelinin adresindeki sayı).

**Kişisel profil** (onay beklemeden hemen; `yazar_turu: "person"`):
1. Uygulamaya **Share on LinkedIn** ve **Sign In with LinkedIn using OpenID Connect**
   ürünlerini ekleyin (anında açılır).
2. Developer portaldaki *OAuth Token Tools* ile `openid profile w_member_social` kapsamlı
   token alın. `https://api.linkedin.com/v2/userinfo` yanıtındaki `sub` değeri →
   `LINKEDIN_AUTHOR_URN` = `urn:li:person:<sub>`.

Gizli anahtarlar: `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AUTHOR_URN`
⚠️ LinkedIn tokenları **60 günde** sona erer; takvime yenileme hatırlatması koyun.

### 2.5 Deneme
**Actions → "Yargıtay kararı paylaş" → Run workflow** ile elle çalıştırın. İsterseniz önce
yalnızca bir platformu deneyin (`platform` kutusuna `x` yazın).

## 3. Ayarlar (`config.yaml`)
| Ayar | Ne işe yarar |
|---|---|
| `buro.imza` | Görselin altındaki kullanıcı adı / web adresi |
| `onay_zorunlu` | `true` iken yalnızca `onay: true` kararlar paylaşılır |
| `platformlar` | Bir platformu kapatmak için `false` |
| `renkler` | Kart renkleri (altın sarısı tema) |
| `hashtagler` | Konuya göre otomatik eklenen etiketler |

Günleri/saati değiştirmek: `.github/workflows/paylas.yml` → `cron: "0 7 * * 1,2,4,5"`
(saat UTC'dir; Türkiye = UTC+3 → `7` = 10:00).

## 4. Meslek kuralları hatırlatması
Paylaşımlar bilgilendirme amaçlı kurgulanmıştır: her gönderiye "hukuki danışmanlık niteliği
taşımaz" notu eklenir, müvekkil/taraf bilgisi ve reklam ifadesi yoktur. Avukatlık Kanunu
m. 55 ve TBB Reklam Yasağı Yönetmeliği çerçevesinde metinleri yine de son kez sizin
kontrol etmeniz için onay adımı vardır.
