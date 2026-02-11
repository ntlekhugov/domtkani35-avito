# Avito XML Autoload: правила генерации

> Источник: документация Avito autoload (https://www.avito.ru/autoload/documentation/templates)
> Проверено: 2026-02-11

## Категория для тканей

**Единственный рабочий путь в XML autoload:**

```
Category: Мебель и интерьер
  GoodsType: Текстиль и ковры
    GoodsSubType: Ткани
```

**Важно:** категория `Хобби и отдых → Рукоделие` НЕ существует в XML autoload.
Аксессуары (молнии, нитки, ленты) и пряжу через XML загрузить нельзя.

## Обязательные поля для ткани

| Поле | Значение |
|------|----------|
| `<Category>` | `Мебель и интерьер` |
| `<GoodsType>` | `Текстиль и ковры` |
| `<GoodsSubType>` | `Ткани` |
| `<AdType>` | `Товар куплен на продажу` |
| `<Condition>` | `Новое` |
| `<Availability>` | `В наличии` |
| `<SubType>` | `Ткань на отрез` / `Наполнители` / `Лоскуты` |
| `<TextileType>` | Одно из 38 значений (см. ниже) |
| `<MainCompositionComponent>` | Одно из 18 значений (см. ниже) |
| `<Title>` | До 100 символов |
| `<Description>` | До 7500 символов |
| `<Price>` | Целое число в рублях |
| `<Images>` | До 10 шт, JPEG/PNG, мин. 400x300 |

## Допустимые значения TextileType (38 шт.)

Атлас, Бархат, Блэкаут, Бязь, Вельвет, Велюр, Габардин, Гобелен,
Дак, Деним, Жаккард, Креп, Кримплен, Кулирка, Лён, Махра,
Микрофибра, Муслин, Неопрен, Нетканый материал, Оксфорд, Перкаль,
Плащёвка, Полисатин, Поплин, Ранфорс, Рогожка, Сатин, Сатин-жаккард,
Сетка, Ситец, Страйп-сатин, Твил, Трикотаж, Фланель, Флис,
Штапель, Экокожа

**НЕ допустимые** (маппим на ближайшие):
- Тюль, Вуаль, Органза, Шифон → `Сетка`
- Тафта → `Атлас`
- Батист → `Поплин`
- Канвас → `Габардин`
- Софт, Шенилл → `Велюр`
- `Другое` — не валидное значение, нельзя использовать как fallback

## Допустимые значения "Основной материал" (18 шт.)

Акрил, Бамбук, Вискоза, Кашемир, Кожа, Лён, Мех, Модал, Нейлон,
Полипропилен, Полиэстер, Полиэфирное волокно, Тенсель, Хлопок,
Шёлк, Шерсть, Эвкалиптовое волокно, Эластан

## Допустимые значения "Для чего подойдёт" (9 шт.)

Постельное бельё, Домашний текстиль, Шторы, Мебель, Пэчворк,
Рукоделие, Пошив одежды, Подкладка, Автомобиль

## Допустимые значения "Подтип товара" (3 шт.)

Ткань на отрез, Наполнители, Лоскуты

## Структура XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Ads formatVersion="3" target="Avito.ru">
  <Ad>
    <Id>domtkani-slug</Id>
    <Category>Мебель и интерьер</Category>
    <GoodsType>Текстиль и ковры</GoodsType>
    <GoodsSubType>Ткани</GoodsSubType>
    <AdType>Товар куплен на продажу</AdType>
    <Condition>Новое</Condition>
    <Availability>В наличии</Availability>
    <SubType>Ткань на отрез</SubType>
    <MainCompositionComponent>Хлопок</MainCompositionComponent>
    <TextileType>Поплин</TextileType>
    <Purpose>
      <Option>Постельное бельё</Option>
    </Purpose>
    <Title>Поплин "Розы", хлопок 100%, ш.2.2м</Title>
    <Description>...</Description>
    <Price>450</Price>
    <Images>
      <Image url="http://domtkani35.ru/wp-content/uploads/..."/>
    </Images>
    <Address>Вологда, Торговая площадь, 11А</Address>
    <ContactPhone>88172724197</ContactPhone>
    <ManagerName>Менеджер</ManagerName>
    <AllowEmail>Да</AllowEmail>
  </Ad>
</Ads>
```

## Скрипт генерации

`scripts/generate_avito_xml.py` — читает `data/processed/products.json`, генерирует XML.

```bash
# Все ткани
python3 scripts/generate_avito_xml.py --output avito_all_feed.xml

# Только лён
python3 scripts/generate_avito_xml.py --filter linen --output avito_linen_feed.xml
```

## Проверка XML

Валидатор: https://autoload.avito.ru/format/xmlcheck/

Быстрая проверка локально:
```bash
# Валидный XML?
python3 -c "import xml.etree.ElementTree as ET; tree = ET.parse('avito_all_feed.xml'); print(f'{len(tree.findall(\".//Ad\"))} ads OK')"

# Какие TextileType используются?
grep -o '<TextileType>[^<]*</TextileType>' avito_all_feed.xml | sort | uniq -c | sort -rn

# Нет ли "Хобби и отдых"?
grep -c 'Хобби и отдых' avito_all_feed.xml
```
