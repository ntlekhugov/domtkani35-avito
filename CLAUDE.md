# Дом Тканей 35 — CLAUDE.md

## Проект

Интернет-магазин тканей domtkani35.ru (Вологда).
Основная задача — выгрузка каталога на Avito через XML autoload.

## Ключевые файлы

| Файл | Назначение |
|------|-----------|
| `scripts/generate_avito_xml.py` | Генерация Avito XML из products.json |
| `data/processed/products.json` | 960 товаров, спарсенных с сайта |
| `avito_all_feed.xml` | Готовый XML для загрузки на Avito |
| `docs/avito-xml-rules.md` | Все правила Avito XML: категории, допустимые значения полей, структура |

## Avito XML — краткие правила

Подробнее: `docs/avito-xml-rules.md`

- Ткани: `Category=Мебель и интерьер`, `GoodsType=Текстиль и ковры`, `GoodsSubType=Ткани`
- Аксессуары и пряжу через XML загрузить нельзя (нет валидной категории)
- `TextileType` — строго 38 значений (список в docs/avito-xml-rules.md), `Другое` невалидно
- Title до 100 символов, Description до 7500
- Валидатор: https://autoload.avito.ru/format/xmlcheck/

## Контакты магазина

- Адрес: Вологда, Торговая площадь, 11А
- Телефон: 88172724197
- Бренд: Николь
