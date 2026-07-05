# CATALEYA · Сервис-бук команды

Онбординг-презентация для официантов кафе-оранжереи **CATALEYA** (сеть FORNO GROUP).
Единый HTML-файл, 58 слайдов, фиксированная сцена 16:9 (1920×1080), без зависимостей.

## Просмотр локально
Открыть **`index.html`** в браузере.
Навигация: `←/→` или свайп · `M` — содержание · `F` — полный экран.

## Просмотр с телефона
- **Горизонтально (рекомендуется):** слайд заполняет весь экран.
- В вертикальном режиме показывается подсказка «Поверните телефон» — её можно закрыть и листать вертикально.

## Публикация на GitHub Pages
Репозиторий уже инициализирован и закоммичен. Осталось создать репозиторий на GitHub и запушить:

```bash
# 1. Создайте пустой репозиторий на github.com (например, cataleya-service-book)
# 2. В этой папке:
git remote add origin https://github.com/<ВАШ_ЛОГИН>/<РЕПОЗИТОРИЙ>.git
git branch -M main
git push -u origin main
```

Затем в репозитории: **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: `main` / `(root)` → Save.**

Через 1–2 минуты сайт будет доступен по адресу:
`https://<ВАШ_ЛОГИН>.github.io/<РЕПОЗИТОРИЙ>/`

Файл `.nojekyll` уже добавлен — GitHub Pages отдаёт все папки как есть.

## Структура
- `index.html` — сам дек (редактировать здесь).
- `cataleya-service-book.html` — редирект на `index.html` (для старых ссылок).
- `assets/img/` — оптимизированные изображения, которые грузит дек (в т.ч. `restaurants/` для bento-слайда).
- `assets/fonts/`, `assets/brand/` — шрифты и логотипы.
- `assets/generated/`, `assets/photos/` — исходники (не попадают в git, см. `.gitignore`).

## Регенерация изображений
Картинки генерируются в `assets/generated/*.png` через `python3 gen_images.py manifest.json`
(kie.ai GPT-Image-2), затем конвертируются в `assets/img/` через `sips` (png→jpg, иконки — png).
Фото ресторанов лежат в `../assets/restaurants/`.
