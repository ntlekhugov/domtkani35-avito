#!/usr/bin/env python3
"""
Generate Avito Autoload XML feed from parsed domtkani35.ru products.
Reads products.json → generates avito_feed.xml

Only fabric products are supported — Avito XML autoload requires:
  Category: Мебель и интерьер → Текстиль и ковры → Ткани

Accessories/yarn are excluded (no valid Avito XML autoload category).

Usage:
  python3 generate_avito_xml.py                    # all fabrics
  python3 generate_avito_xml.py --filter linen     # linen only
  python3 generate_avito_xml.py --phone 88172724197 --address "Вологда, Торговая площадь, 11А"
"""

import json
import argparse
import html
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / 'data'
PRODUCTS_FILE = DATA_DIR / 'processed' / 'products.json'
OUTPUT_FILE = DATA_DIR / 'processed' / 'avito_feed.xml'

# Defaults — contact info for the store employee
DEFAULT_PHONE = '88172724197'
DEFAULT_ADDRESS = 'Вологда, Торговая площадь, 11А'
DEFAULT_MANAGER = 'Менеджер'

DEFAULT_AD_TYPE = 'Товар куплен на продажу'

# --- Product type classification ---

# Keywords in title that indicate non-fabric products (accessories/haberdashery)
ACCESSORY_KEYWORDS = [
    'пряжа', 'молния', 'молнии', 'нитки', 'нить', 'игл',
    'люверс', 'лента', 'тесьма', 'пуговиц', 'кнопк', 'булавк',
    'ножниц', 'наперст', 'сантиметр', 'мел ',
    'подхват', 'крючки для', 'зажим', 'кисточк', 'стразы',
    'стеклярус', 'бисер', 'шнур витой', 'шнур декор',
    'кант декоративн', 'вьюнчик', 'рюш', 'сутаж',
    'плечевые накладк', 'товары для кроя', 'товары для бисер',
    'клеевые материал', 'клеевые написал',
    'коробк', 'штурнная лента', 'shtornaya lenta',
]

# Keywords that specifically indicate yarn (subset of accessories)
YARN_KEYWORDS = ['пряжа']

# --- Material detection ---

# Mapping composition/title text → Avito "Основной материал" values
MATERIAL_MAP = {
    'лен': 'Лён',
    'лён': 'Лён',
    'льн': 'Лён',
    'х/б': 'Хлопок',
    'х\\б': 'Хлопок',
    'хлопок': 'Хлопок',
    'хлоп': 'Хлопок',
    'полиэстер': 'Полиэстер',
    'полиэфир': 'Полиэстер',
    'вискоза': 'Вискоза',
    'шерсть': 'Шерсть',
    'шёлк': 'Шёлк',
    'шелк': 'Шёлк',
    'акрил': 'Акрил',
    'нейлон': 'Нейлон',
    'капрон': 'Нейлон',
    'эластан': 'Эластан',
    'спандекс': 'Эластан',
    'кашемир': 'Кашемир',
    'бамбук': 'Бамбук',
}

# Mapping title keywords → Avito "Для чего подойдёт" (Purpose)
PURPOSE_MAP = {
    'мебельн': 'Мебель',
    'шторн': 'Шторы',
    'портьер': 'Шторы',
    'тюль': 'Шторы',
    'вуаль': 'Шторы',
    'органз': 'Шторы',
    'блэкаут': 'Шторы',
    'постельн': 'Постельное бельё',
    'бязь': 'Постельное бельё',
    'сатин': 'Постельное бельё',
    'поплин': 'Постельное бельё',
    'платель': 'Пошив одежды',
    'рубашеч': 'Пошив одежды',
    'сорочеч': 'Пошив одежды',
    'костюмн': 'Пошив одежды',
    'блузоч': 'Пошив одежды',
    'подкладк': 'Подкладка',
    'живопис': 'Рукоделие',
    'лоскут': 'Пэчворк',
    'столов': 'Домашний текстиль',
    'полотенц': 'Домашний текстиль',
    'автомобил': 'Автомобиль',
    'авточехл': 'Автомобиль',
}

# Mapping title/composition keywords → Avito "Тип ткани" (TextileType)
# Valid Avito values: Атлас, Бархат, Блэкаут, Бязь, Вельвет, Велюр,
# Габардин, Гобелен, Дак, Деним, Жаккард, Креп, Кримплен, Кулирка,
# Лён, Махра, Микрофибра, Муслин, Неопрен, Нетканый материал,
# Оксфорд, Перкаль, Плащёвка, Полисатин, Поплин, Ранфорс, Рогожка,
# Сатин, Сатин-жаккард, Сетка, Ситец, Страйп-сатин, Твил,
# Трикотаж, Фланель, Флис, Штапель, Экокожа
TEXTILE_TYPE_MAP = {
    # Direct matches (value exists in Avito's list)
    'жаккард': 'Жаккард',
    'сатин': 'Сатин',
    'сатен': 'Сатин',
    'бязь': 'Бязь',
    'вельвет': 'Вельвет',
    'велюр': 'Велюр',
    'габардин': 'Габардин',
    'гобелен': 'Гобелен',
    'деним': 'Деним',
    'креп': 'Креп',
    'муслин': 'Муслин',
    'рогожк': 'Рогожка',
    'атлас': 'Атлас',
    'поплин': 'Поплин',
    'штапел': 'Штапель',
    'трикотаж': 'Трикотаж',
    'футер': 'Трикотаж',
    'кулирк': 'Кулирка',
    'флис': 'Флис',
    'фланел': 'Фланель',
    'твил': 'Твил',
    'перкал': 'Перкаль',
    'блэкаут': 'Блэкаут',
    'экокож': 'Экокожа',
    'замш': 'Экокожа',
    'сетк': 'Сетка',
    'махр': 'Махра',
    'плащёвк': 'Плащёвка',
    'плащевк': 'Плащёвка',
    'микрофибр': 'Микрофибра',
    'оксфорд': 'Оксфорд',
    'ситец': 'Ситец',
    'бархат': 'Бархат',
    'лён': 'Лён',
    'льн': 'Лён',
    'лен': 'Лён',
    'ранфорс': 'Ранфорс',
    'полисатин': 'Полисатин',
    'неопрен': 'Неопрен',
    'кримплен': 'Кримплен',
    'дак': 'Дак',
    # Mapped to closest valid Avito value
    'тюль': 'Сетка',
    'вуаль': 'Сетка',
    'органз': 'Сетка',
    'тафт': 'Атлас',
    'шифон': 'Сетка',
    'батист': 'Поплин',
    'канвас': 'Габардин',
    'софт': 'Велюр',
    'шенилл': 'Велюр',
    # Additional keywords for products that had no match
    'камуфляж': 'Плащёвка',
    'плащев': 'Плащёвка',
    'сорочеч': 'Поплин',
    'рубашеч': 'Поплин',
    'костюмн': 'Габардин',
    'журавинк': 'Жаккард',
    'портерн': 'Жаккард',
    'портьер': 'Жаккард',
    'тентов': 'Оксфорд',
    'палаточ': 'Оксфорд',
}

# Product filters — keywords and exclusions
FILTERS = {
    'linen': {
        'keywords': ['лён', 'льн', 'лен'],
        'exclude_titles': ['лента', 'тесьма', 'люверсная'],
        'require_images': True,
    },
    'fabrics': {
        'type': 'fabric',
        'require_images': True,
    },
}


def classify_product(product):
    """Classify product as 'fabric', 'accessory', or 'yarn'"""
    title = product.get('title', '').lower()

    if not title:
        return 'skip'

    for kw in YARN_KEYWORDS:
        if kw in title:
            return 'yarn'

    for kw in ACCESSORY_KEYWORDS:
        if kw in title:
            return 'accessory'

    return 'fabric'


def match_filter(product, filter_config):
    """Check if product matches a named filter"""
    # Type-based filter
    if 'type' in filter_config:
        if classify_product(product) != filter_config['type']:
            return False
        if filter_config.get('require_images') and not product.get('images'):
            return False
        return True

    # Keyword-based filter
    title = product.get('title', '').lower()
    comp = product.get('composition', '').lower()
    desc = product.get('description', '').lower()
    text = f'{title} {comp} {desc}'

    if not any(kw in text for kw in filter_config['keywords']):
        return False

    if any(ex in title for ex in filter_config.get('exclude_titles', [])):
        return False

    if filter_config.get('require_images') and not product.get('images'):
        return False

    return True


def apply_filter(products, filter_name):
    """Filter products by named filter, return filtered list"""
    if filter_name not in FILTERS:
        print(f'ERROR: unknown filter "{filter_name}". Available: {", ".join(FILTERS.keys())}')
        return []

    config = FILTERS[filter_name]
    filtered = [p for p in products if match_filter(p, config)]
    print(f'Filter "{filter_name}": {len(filtered)} of {len(products)} products matched')
    return filtered


def detect_material(product):
    """Detect Avito material from product composition/title"""
    text = f'{product.get("composition", "")} {product.get("title", "")}'.lower()
    for keyword, material in MATERIAL_MAP.items():
        if keyword in text:
            return material
    return 'Полиэстер'


def detect_purpose(product):
    """Detect Avito purpose from product title"""
    title = product.get('title', '').lower()
    purposes = set()
    for keyword, purpose in PURPOSE_MAP.items():
        if keyword in title:
            purposes.add(purpose)
    if not purposes:
        purposes = {'Рукоделие', 'Пошив одежды'}
    return purposes


def detect_textile_type(product):
    """Detect Avito TextileType from product title/composition.
    Falls back to material-based guess when no keyword matches.
    """
    title = product.get('title', '').lower()
    comp = product.get('composition', '').lower()
    text = f'{title} {comp}'

    for keyword, textile_type in TEXTILE_TYPE_MAP.items():
        if keyword in text:
            return textile_type

    # Material-based fallback (all values are valid Avito TextileType)
    if 'хлопок' in text or 'х/б' in text or 'хлоп' in text:
        return 'Поплин'
    if 'полиэстер' in text or 'полиэфир' in text:
        return 'Атлас'
    if 'вискоза' in text:
        return 'Креп'
    if 'шерсть' in text:
        return 'Габардин'
    if 'шёлк' in text or 'шелк' in text:
        return 'Атлас'

    return 'Поплин'


def escape_xml(text):
    """Escape special XML characters"""
    if not text:
        return ''
    return html.escape(str(text), quote=False)


def build_title(product):
    """Build Avito title (max 100 chars per Avito docs)"""
    title = product.get('title', '')
    composition = product.get('composition', '')
    width = product.get('width', '')

    if composition and width:
        full = f'{title}, {composition}, ш.{width}'
    elif composition:
        full = f'{title}, {composition}'
    elif width:
        full = f'{title}, ш.{width}'
    else:
        full = title

    if len(full) <= 100:
        return full

    if composition:
        short = f'{title}, {composition}'
        if len(short) <= 100:
            return short

    return title[:100]


def build_description(product, product_type='fabric'):
    """Build rich description for Avito listing"""
    lines = []
    title = product.get('title', '')

    if product_type == 'fabric':
        lines.append(f'Ткань "{title}"')
    elif product_type == 'yarn':
        lines.append(f'{title}')
    else:
        lines.append(f'{title}')

    lines.append('')

    manufacturer = product.get('manufacturer', '')
    composition = product.get('composition', '')
    width = product.get('width', '')

    if manufacturer:
        lines.append(f'Производитель: {manufacturer}')
    if composition:
        lines.append(f'Состав: {composition}')
    if width:
        lines.append(f'Ширина: {width}')

    if product.get('description'):
        lines.append('')
        lines.append(product['description'])

    lines.append('')
    if product_type == 'fabric':
        lines.append('Цена указана за 1 метр.')
    else:
        lines.append('Цена указана за 1 шт.')
    lines.append('')
    lines.append('Магазин "Николь" — сеть магазинов ткани')
    lines.append('г. Вологда, Торговая пл., д.11-а')
    lines.append('Пн-Пт 10:00-19:00, Сб 10:00-18:00, Вс 10:00-17:00')
    lines.append('Тел: 8(8172) 72-41-97')

    return '\n'.join(lines)


def generate_ad_fabric(p, phone, address, manager_name):
    """Generate <Ad> XML for a fabric product"""
    lines = []
    ad_id = f'domtkani-{p.get("slug", "")}'
    title = build_title(p)
    description = build_description(p, 'fabric')
    price = p.get('price', 0)
    images = p.get('images', [])

    material = detect_material(p)
    textile_type = detect_textile_type(p)
    purposes = detect_purpose(p)

    lines.append('  <Ad>')
    lines.append(f'    <Id>{escape_xml(ad_id)}</Id>')
    lines.append(f'    <Category>Мебель и интерьер</Category>')
    lines.append(f'    <GoodsType>Текстиль и ковры</GoodsType>')
    lines.append(f'    <GoodsSubType>Ткани</GoodsSubType>')
    lines.append(f'    <AdType>{DEFAULT_AD_TYPE}</AdType>')
    lines.append(f'    <Condition>Новое</Condition>')
    lines.append(f'    <Availability>В наличии</Availability>')
    lines.append(f'    <SubType>Ткань на отрез</SubType>')
    lines.append(f'    <MainCompositionComponent>{escape_xml(material)}</MainCompositionComponent>')
    lines.append(f'    <TextileType>{escape_xml(textile_type)}</TextileType>')

    if purposes:
        lines.append('    <Purpose>')
        for purpose in sorted(purposes):
            lines.append(f'      <Option>{escape_xml(purpose)}</Option>')
        lines.append('    </Purpose>')

    lines.append(f'    <Title>{escape_xml(title)}</Title>')
    lines.append(f'    <Description>{escape_xml(description)}</Description>')
    lines.append(f'    <Price>{price}</Price>')

    if images:
        lines.append('    <Images>')
        for img_url in images[:10]:
            lines.append(f'      <Image url="{escape_xml(img_url)}"/>')
        lines.append('    </Images>')

    lines.append(f'    <Address>{escape_xml(address)}</Address>')
    lines.append(f'    <ContactPhone>{escape_xml(phone)}</ContactPhone>')
    lines.append(f'    <ManagerName>{escape_xml(manager_name)}</ManagerName>')
    lines.append(f'    <AllowEmail>Да</AllowEmail>')
    lines.append('  </Ad>')
    return lines


def generate_xml(products, phone, address, manager_name):
    """Generate Avito Autoload XML — fabrics only (no valid category for accessories/yarn)"""
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<Ads formatVersion="3" target="Avito.ru">')
    lines.append(f'<!-- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} -->')
    lines.append(f'<!-- Products: {len(products)} -->')
    lines.append('')

    stats = {'fabric': 0, 'accessory': 0, 'yarn': 0, 'skipped': 0}

    for p in products:
        title = p.get('title', '')
        if not title or not p.get('price'):
            stats['skipped'] += 1
            continue

        if not p.get('images'):
            stats['skipped'] += 1
            continue

        product_type = classify_product(p)

        if product_type == 'fabric':
            ad_lines = generate_ad_fabric(p, phone, address, manager_name)
            stats['fabric'] += 1
            lines.extend(ad_lines)
            lines.append('')
        else:
            stats[product_type] += 1

    lines.append('</Ads>')

    print(f'Generated: {stats["fabric"]} fabric ads')
    print(f'Excluded: {stats["accessory"]} accessories, {stats["yarn"]} yarn (no valid Avito XML category)')
    print(f'Skipped: {stats["skipped"]} (no title/price/images)')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Generate Avito XML feed')
    parser.add_argument('--phone', default=DEFAULT_PHONE, help='Contact phone')
    parser.add_argument('--address', default=DEFAULT_ADDRESS, help='Store address')
    parser.add_argument('--manager', default=DEFAULT_MANAGER, help='Manager name')
    parser.add_argument('--input', default=str(PRODUCTS_FILE), help='Input JSON file')
    parser.add_argument('--output', default=None, help='Output XML file')
    parser.add_argument('--filter', default=None, help=f'Product filter: {", ".join(FILTERS.keys())}')
    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    elif args.filter:
        output_path = DATA_DIR / 'processed' / f'avito_{args.filter}_feed.xml'
    else:
        output_path = OUTPUT_FILE

    # Load products
    input_path = Path(args.input)
    if not input_path.exists():
        progress = DATA_DIR / 'raw' / '_progress.json'
        if progress.exists():
            print(f'products.json not found, using progress file...')
            with open(progress) as f:
                data = json.load(f)
            products = data.get('products', [])
        else:
            print(f'ERROR: No product data found at {input_path}')
            return
    else:
        with open(input_path) as f:
            products = json.load(f)

    print(f'Loaded {len(products)} products')

    # Apply filter if specified
    if args.filter:
        products = apply_filter(products, args.filter)
        if not products:
            return

    # Generate XML
    xml_content = generate_xml(products, args.phone, args.address, args.manager)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    print(f'Saved to {output_path} ({output_path.stat().st_size / 1024:.1f} KB)')


if __name__ == '__main__':
    main()
