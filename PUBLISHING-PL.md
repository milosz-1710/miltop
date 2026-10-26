# Jak opublikować miltop na GitHubie

## 1. Przygotuj zrzuty ekranu

Główny zrzut `dashboard.jpg` jest już dodany do `README.md`. Nazwy opcjonalnych
dodatkowych zrzutów znajdują się w `docs/screenshots/README.md`.

Przed publikacją sprawdź, czy na zrzutach nie ma prywatnych danych.

## 2. Utwórz puste repozytorium

1. Wejdź na https://github.com/new i zaloguj się jako `milosz-1710`.
2. W polu **Repository name** wpisz `miltop`.
3. Wybierz **Public**.
4. Nie zaznaczaj dodawania README, `.gitignore` ani licencji — te pliki są już
   przygotowane lokalnie.
5. Kliknij **Create repository**.

Opis do pola **Description**:

> A lightweight, tile-based system monitor and process manager for Linux terminals.

Proponowane tematy (**Topics**):

`linux`, `terminal`, `tui`, `system-monitor`, `process-manager`, `python`, `curses`

## 3. Wyślij przygotowane pliki

W terminalu wykonaj:

```bash
cd /home/milosz/Documents/miltop
git init -b main
git add .
git commit -m "Initial public release of miltop"
git remote add origin https://github.com/milosz-1710/miltop.git
git push -u origin main
```

Jeśli Git poprosi o dane autora, ustaw je wcześniej:

```bash
git config --global user.name "Miłosz"
git config --global user.email "79249752+milosz-1710@users.noreply.github.com"
```

Dokładny prywatny adres `noreply` skopiujesz z GitHub: **Settings → Emails →
Keep my email addresses private**. Dzięki temu commit zostanie przypisany do
Twojego konta bez ujawniania prywatnego adresu.

Przy wysyłaniu przez HTTPS GitHub nie przyjmuje hasła do konta. Najwygodniej
zalogować się przez GitHub CLI (`gh auth login`) albo użyć klucza SSH/tokena.

## 4. Uzupełnij stronę repozytorium

Na stronie projektu kliknij ikonę koła zębatego obok **About**, wklej opis i
dodaj Topics wymienione wyżej. Włącz **Issues**, aby użytkownicy mogli zgłaszać
błędy.

## 5. Opublikuj pierwsze wydanie

Po sprawdzeniu repozytorium:

```bash
git tag -a v1.1.0 -m "miltop 1.1.0"
git push origin v1.1.0
```

Następnie na GitHubie wybierz **Releases → Draft a new release**, wskaż tag
`v1.1.0`, ustaw tytuł `miltop 1.1.0` i wklej sekcję wersji 1.1.0 z
`CHANGELOG.md`.

## 6. Paczki dystrybucyjne

Najpierw warto opublikować i przetestować kod źródłowy. Kolejny krok to
automatyczne budowanie:

- wheel/source archive dla `pipx` i PyPI;
- `.deb` dla Debiana/Ubuntu/Minta;
- `.rpm` dla Fedory (lokalna instalacja przez DNF);
- `PKGBUILD` dla AUR.

Repozytorium COPR można dodać później, aby Fedora aktualizowała miltop przez
zwykłe `dnf upgrade`. AUR publikuje przepis `PKGBUILD`, a nie gotowy oficjalny
pakiet Arch Linux.

## Co oznacza GPL-3.0-or-later

Każdy może używać, kopiować, analizować i zmieniać program. Jeśli ktoś
publicznie rozpowszechnia zmodyfikowaną wersję, musi również udostępnić jej kod
źródłowy na zgodnej licencji GPL. Autorstwo nadal należy do Ciebie, a licencja
nie daje gwarancji działania programu.
