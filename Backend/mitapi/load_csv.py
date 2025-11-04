import csv
from django.core.management import BaseCommand
from django.utils import timezone

# from products.models import ProductCategory, Product


class Command(BaseCommand):
    help = "Loads products and product categories from CSV file."

    def add_arguments(self, parser):
        self.stdout.write(
            self.style.SUCCESS(
                f"add_arguments."
            )
        )
        parser.add_argument("file_path", type=str)

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                f"handle."
            )
        )

        start_time = timezone.now()
        file_path = options["file_path"]
        with open(file_path, "r") as csv_file:
            data = csv.reader(csv_file, delimiter=",")
            # product_categories = {p_category.code: p_category for p_category in ProductCategory.objects.all()}
            # products = []
            # for row in data:
            #     product_category_code = row[4]
            #     product_category = product_categories.get(product_category_code)
            #     if not product_category:
            #         product_category = ProductCategory.objects.create(name=row[3], code=row[4])
            #         product_categories[product_category.code] = product_category
            #     product = Product(
            #         name=row[0],
            #         code=row[1],
            #         price=row[2],
            #         product_category=product_category
            #     )
            #     products.append(product)
            #     if len(products) > 5000:
            #         Product.objects.bulk_create(products)
            #         products = []
            # if products:
            #     Product.objects.bulk_create(products)
        end_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(
                f"Loading CSV took: {(end_time-start_time).total_seconds()} seconds."
            )
        )
