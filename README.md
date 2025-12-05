# 🎯 Git Compliance Checker System
Sistem untuk monitoring dan validasi compliance commits & merge requests berdasarkan standar format tertentu.

## 📋 Gambaran Masalah

Beberapa masalah dalam development:

1. **Inkonsistensi Format Commit**
2. **Link Dokumentasi Tidak Terorganisir (Taiga & Testing)**
3. **Kesulitan Audit & Tracking Code Changes/Ticket Project**
4. **Testing Evidence Tidak Terdokumentasi**

## ✅ Solusi Masalah

Git Compliance Checker menyediakan:

### 1. **Standarisasi Format Commit & MR Title**
Format yang diharuskan:
```
<tipe>: <ringkasan singkat> (Taiga #<NamaProject>-<NomorTicket>)
```

**Contoh:**
```
feat: Tambah fitur authentication (Taiga #DATB-123)
fix: Perbaiki bug login timeout (Taiga #DATB-456)
docs: Update API documentation (Taiga #DATB-789)
```

**Tipe Commit yang Valid:**
- `feat` - Fitur baru
- `fix` - Bug fix
- `docs` - Perubahan dokumentasi
- `style` - Formatting, semicolon, dll (tidak mengubah logic)
- `refactor` - Refactoring code
- `perf` - Peningkatan performance
- `test` - Menambah atau memperbaiki test
- `chore` - Maintenance task
- `build` - Perubahan build system
- `ci` - Perubahan CI configuration
- `revert` - Revert commit sebelumnya

### 2. **Ekstraksi Link Otomatis**
Sistem dapat mengekstrak link penting dari deskripsi MR:

```markdown
Ticket Link: [(Taiga #DATB-456)](https://projects.digitaltelkom.id/project/DATB/us/10353)
Documentation Link: [Figma](https://www.figma.com/design/example)
Testing Link: [https://testing.example.com/result/123]
```

### 3. **Validasi Real-time**
- Validasi format title
- Validasi tipe commit
- Error messages yang jelas
- Saran perbaikan yang actionable

## 📁 Struktur Project
```
GIT-COMPLIANCE-CHECKER/
├── index.html                # HTML demo interaktif untuk testing via browser
├── git_validator.py          # Core validator commit/MR compliance (Python model)
├── unit_test_validator.py    # Automated tests untuk validator
└── README.md                 # Dokumentasi ini
```

## 🚀 Cara Menjalankan Program

### Persyaratan
- Python 3.7 atau lebih tinggi
- **TIDAK PERLU** install library tambahan (menggunakan standard library)

### Instalasi
- Clone atau Download File
   ```bash
   git clone https://github.com/kaniraerlna/git-compliance-checker.git
   cd git-compliance-checker
   ```

### Menjalankan Program

#### 1. Run Demo Built-in

Jalankan file langsung untuk melihat demo:

```bash
python git_compliance_checker.py
```

Output akan menampilkan 3 test cases:
- ✅ Valid title
- ❌ Invalid title - Missing Taiga Reference
- 🔗 MR with Links Extraction

#### 2. Run Demo HTML (Browser)

Buka file index.html di browser:

```bash
# Cara 1: Double-click file index.html
# Cara 2: Dari terminal
open index.html           # macOS
start index.html          # Windows
xdg-open index.html       # Linux
```

Cara menggunakan:
- Masukkan commit title di tab "Commit Checker", lalu klik tombol "Validate Title"
- Masukkan MR title dan MR Reference Extraction di tab "MR Checker", lalu klik tombol "Validate Title"
- Lihat hasil validasi dan extraction link di bagian bawah

## 📖 Contoh Penggunaan

### Valid Examples

✅ **CORRECT:**
```
feat: Tambah halaman dashboard analytics (Taiga #DATB-123)
fix: Perbaiki memory leak pada service worker (Taiga #PROJ-456)
docs: Update README dengan panduan deployment (Taiga #CORE-789)
```

### Invalid Examples

❌ **INCORRECT:**
```
# Missing Taiga reference
feat: Tambah halaman dashboard

# Wrong format
Feature: Added dashboard (Taiga #DATB-123)

# No space after colon
feat:Tambah halaman dashboard (Taiga #DATB-123)

# Invalid type
feature: Tambah dashboard (Taiga #DATB-123)

# Summary too short
feat: Add page (Taiga #DATB-123)

# Wrong Taiga format
feat: Tambah dashboard (DATB-123)
```

## 🔧 Konfigurasi

### Mengubah Valid Types

Edit di `TitleComplianceChecker`:

```python
VALID_TYPES = [
    'feat', 'fix', 'docs', 'style', 'refactor', 
    'perf', 'test', 'chore', 'build', 'ci', 'revert',
    'hotfix'  # Tambah custom type
]
```

### Mengubah Panjang Summary

Edit di method `check_compliance`:

```python
# Minimum length
if len(summary) < 10:  # Ubah sesuai kebutuhan

# Maximum length  
if len(summary) > 100:  # Ubah sesuai kebutuhan
```

### Regex Pattern Custom

Jika format Taiga berbeda, ubah pattern:

```python
TITLE_PATTERN = re.compile(
    r'^(?P<type>[a-z]+):\s+(?P<summary>.+?)\s+\(Taiga\s+#(?P<project>[A-Z0-9]+)-(?P<ticket>\d+)\)$',
    re.IGNORECASE
)
```


**Made with ❤️ for better Git practices**
