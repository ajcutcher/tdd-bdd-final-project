# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model
"""

import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        db.session.close()

    def setUp(self):
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        product = Product(
            name="Fedora",
            description="A red hat",
            price=12.50,
            available=True,
            category=Category.CLOTHS,
        )
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertIsNone(product.id)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertTrue(product.available)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        self.assertEqual(Product.all(), [])
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # NEW TEST CASES
    #
    def test_deserialize_with_missing_data(self):
        with self.assertRaises(DataValidationError):
            Product().deserialize(None)

    def test_deserialize_with_bad_data(self):
        with self.assertRaises(DataValidationError):
            Product().deserialize("not a dict")
    def test_deserialize_invalid_boolean(self):
        product = Product()
        data = {
            "name": "Test",
            "description": "Test",
            "price": 10.00,
            "available": "yes",
            "category": "FOOD"
        }
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_find_by_category_no_results(self):
        products = Product.find_by_category(Category.TOOLS)
        self.assertEqual(len(list(products)), 0)

    def test_update_without_id(self):
        product = ProductFactory()
        product.id = None
        with self.assertRaises(DataValidationError):
            product.update()

    def test_deserialize_missing_required_fields(self):
        data = {"description": "Missing name"}
        with self.assertRaises(DataValidationError):
            Product().deserialize(data)

    def test_find_product_with_invalid_id(self):
        product = Product.find(999999)
        self.assertIsNone(product)

    def test_read_a_product(self):
        product = ProductFactory()
        product.id = None
        product.create()
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        product = ProductFactory()
        product.id = None
        product.create()
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")

    def test_delete_a_product(self):
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        self.assertEqual(Product.all(), [])
        for _ in range(5):
            ProductFactory().create()
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([p for p in products if p.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([p for p in products if p.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([p for p in products if p.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_serialize_a_product(self):
        """It should serialize a Product into a dictionary"""
        product = ProductFactory()
        product.id = None
        product.create()
        data = product.serialize()
        self.assertEqual(data["id"], product.id)
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(data["price"], float(product.price))
        self.assertEqual(data["available"], product.available)
        self.assertEqual(data["category"], product.category.name)

    def test_deserialize_valid_category(self):
        """It should deserialize a valid category string into an enum"""
        data = {
            "name": "Test Product",
            "description": "Test Description",
            "price": 19.99,
            "available": True,
            "category": "CLOTHS",
        }
        product = Product()
        product.deserialize(data)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_deserialize_invalid_category(self):
        """It should raise DataValidationError for invalid category string"""
        data = {
            "name": "Test Product",
            "description": "Test Description",
            "price": 19.99,
            "available": True,
            "category": "INVALID",
        }
        with self.assertRaises(DataValidationError):
            Product().deserialize(data)

