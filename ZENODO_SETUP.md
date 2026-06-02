# Zenodo & GitHub Hazırlığı — Atıf İçin

Bu yazılımın bilimsel olarak atıf yapılabilir olması için aşağıdaki adımları izle.

## 1. GitHub Repository Oluştur

```bash
cd "Gözenek ve Renk Tespit Yazılımı"
git init
git add .
git commit -m "v1.0.0: initial release"
git branch -M main
# GitHub'da boş repo aç, sonra:
git remote add origin https://github.com/<KULLANICI>/pore-color-segmentation.git
git push -u origin main
```

`README.md`, `LICENSE`, `CITATION.cff` ve `requirements.txt` dosyaları otomatik repo köküne kopyalanmış olacak.

## 2. GitHub Release Oluştur

Repo'da Releases → "Draft a new release":
- Tag: `v1.0.0`
- Title: `Gözenek ve Renk Tespit Yazılımı v1.0.0`
- Description: CHANGELOG'dan v1.0.0 bölümünü kopyala

## 3. Zenodo Entegrasyonu (DOI Almak İçin)

1. https://zenodo.org adresine git, GitHub ile giriş yap
2. Profile → Settings → GitHub
3. Repo listesini "Sync" et
4. Pore-color-segmentation reposunu **aç** (toggle ON)
5. GitHub'da yeni release oluştur (v1.0.0)
6. Zenodo otomatik olarak yeni bir DOI atayacak (~10 dakika içinde)
7. DOI formatı: `10.5281/zenodo.XXXXXXX`

## 4. CITATION.cff'i Güncelle

DOI alınca `CITATION.cff` dosyasındaki:
```yaml
doi: "10.5281/zenodo.XXXXXXX"
```
satırını gerçek DOI ile değiştir, commit + push.

## 5. README'ye Atıf Rozeti Ekle

```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![CITATION.cff](https://img.shields.io/badge/cite-CITATION.cff-blue)](CITATION.cff)
```

## 6. Makaleye Software Citation Ekle

Methods bölümünün sonuna:

> **Software Availability:** The interactive segmentation tool developed
> in this study, "Gözenek ve Renk Tespit Yazılımı" v1.0, is freely available
> at [GitHub URL] under MIT license. A versioned release is archived on
> Zenodo (DOI: 10.5281/zenodo.XXXXXXX). For software-specific implementation
> details, see the companion software paper (Sert et al., 2026, SoftwareX,
> in preparation).

## 7. Companion Software Paper

Aynı çalışmadan bir de SoftwareX makalesi çıkar. Şablon:
- https://www.elsevier.com/journals/softwarex/2352-7110/guide-for-authors
- 6 sayfa, struktüre: Motivation, Description, Examples, Impact, Conclusions
- Ana CBM paper'a atıf yap, geri atıf alır

## Atıf Akış Şeması

```
Yazılımı kullanan araştırmacı
        │
        ├─ Yazılıma atıf: Zenodo DOI (CITATION.cff)
        │
        ├─ Software paper'a atıf: SoftwareX (companion)
        │
        └─ Method paper'a atıf: CBM (companion)
```

3 hatlı atıf → maksimum yaygın etki + akademik görünürlük.
