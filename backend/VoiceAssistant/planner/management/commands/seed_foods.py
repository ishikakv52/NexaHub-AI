from django.core.management.base import BaseCommand
from VoiceAssistant.planner.models import Food

FOODS = [
    # Grains - Breakfast
    ('Oats', 389, 16.9, 66.3, 6.9, 'grains', 'breakfast', 'vegetarian', 80),
    ('Poha (Flattened Rice)', 394, 7.0, 89.0, 1.0, 'grains', 'breakfast', 'vegetarian', 150),
    ('Upma (Semolina)', 360, 12.7, 73.0, 1.5, 'grains', 'breakfast', 'vegetarian', 200),
    ('Idli', 39, 2.7, 7.8, 0.2, 'grains', 'breakfast', 'vegetarian', 120),
    ('Dosa (Plain)', 168, 4.0, 28.0, 4.0, 'grains', 'breakfast', 'vegetarian', 150),
    ('Masala Dosa', 220, 6.0, 32.0, 8.0, 'grains', 'breakfast', 'vegetarian', 200),
    ('Paratha (Whole Wheat)', 297, 9.0, 46.0, 9.0, 'grains', 'breakfast', 'vegetarian', 100),
    ('Aloo Paratha', 320, 8.0, 45.0, 12.0, 'grains', 'breakfast', 'vegetarian', 150),
    ('Roti (Whole Wheat)', 297, 11.0, 46.0, 7.0, 'grains', 'any', 'vegetarian', 40),
    ('Brown Rice', 111, 2.6, 23.0, 0.9, 'grains', 'lunch', 'vegetarian', 150),
    ('White Rice', 130, 2.7, 28.0, 0.3, 'grains', 'lunch', 'vegetarian', 150),
    ('Quinoa', 368, 14.1, 64.2, 6.1, 'grains', 'lunch', 'vegetarian', 100),
    ('Millet (Bajra)', 361, 11.0, 67.0, 5.0, 'grains', 'lunch', 'vegetarian', 100),
    ('Ragi (Finger Millet)', 336, 7.3, 72.0, 1.3, 'grains', 'breakfast', 'vegetarian', 100),
    ('Pongal', 150, 4.0, 25.0, 4.0, 'grains', 'breakfast', 'vegetarian', 200),
    ('Uttapam', 180, 5.0, 30.0, 4.0, 'grains', 'breakfast', 'vegetarian', 150),
    ('Appam', 120, 3.0, 22.0, 2.0, 'grains', 'breakfast', 'vegetarian', 100),
    ('Chapati', 297, 11.0, 46.0, 7.0, 'grains', 'any', 'vegetarian', 40),
    ('Khichdi', 130, 4.5, 22.0, 3.0, 'grains', 'dinner', 'vegetarian', 250),
    ('Biryani (Veg)', 180, 5.0, 28.0, 6.0, 'grains', 'lunch', 'vegetarian', 250),

    # Dairy
    ('Milk (Full Fat)', 61, 3.2, 4.8, 3.3, 'dairy', 'any', 'vegetarian', 250),
    ('Milk (Skim)', 34, 3.4, 5.0, 0.1, 'dairy', 'any', 'vegetarian', 250),
    ('Paneer', 265, 18.0, 3.6, 20.0, 'dairy', 'any', 'vegetarian', 100),
    ('Yogurt (Curd)', 59, 3.5, 4.7, 3.3, 'dairy', 'any', 'vegetarian', 150),
    ('Greek Yogurt', 97, 9.0, 3.6, 5.0, 'dairy', 'morning_snack', 'vegetarian', 150),
    ('Buttermilk (Chaas)', 40, 2.0, 4.0, 1.5, 'dairy', 'any', 'vegetarian', 250),
    ('Cheese (Cottage)', 98, 11.0, 3.4, 4.3, 'dairy', 'any', 'vegetarian', 100),
    ('Ghee', 900, 0.0, 0.0, 100.0, 'dairy', 'any', 'vegetarian', 10),
    ('Lassi (Sweet)', 80, 3.0, 12.0, 2.0, 'dairy', 'evening_snack', 'vegetarian', 250),
    ('Lassi (Salted)', 45, 3.0, 5.0, 1.5, 'dairy', 'evening_snack', 'vegetarian', 250),
    ('Kheer (Rice Pudding)', 150, 4.0, 25.0, 4.0, 'dairy', 'evening_snack', 'vegetarian', 150),
    ('Raita', 60, 3.0, 6.0, 2.5, 'dairy', 'lunch', 'vegetarian', 100),

    # Protein - Non Veg
    ('Chicken Breast', 165, 31.0, 0.0, 3.6, 'protein', 'lunch', 'non_vegetarian', 150),
    ('Chicken Curry', 180, 22.0, 5.0, 8.0, 'protein', 'lunch', 'non_vegetarian', 200),
    ('Egg (Boiled)', 155, 13.0, 1.1, 11.0, 'protein', 'breakfast', 'non_vegetarian', 50),
    ('Egg Omelette', 154, 11.0, 1.0, 12.0, 'protein', 'breakfast', 'non_vegetarian', 100),
    ('Egg Bhurji', 170, 12.0, 3.0, 12.0, 'protein', 'breakfast', 'non_vegetarian', 150),
    ('Fish (Rohu)', 97, 19.0, 0.0, 2.0, 'protein', 'lunch', 'non_vegetarian', 150),
    ('Fish Curry', 120, 18.0, 4.0, 4.0, 'protein', 'lunch', 'non_vegetarian', 200),
    ('Prawns', 99, 24.0, 0.2, 0.3, 'protein', 'lunch', 'non_vegetarian', 100),
    ('Mutton Curry', 250, 20.0, 5.0, 17.0, 'protein', 'dinner', 'non_vegetarian', 200),
    ('Tandoori Chicken', 175, 27.0, 2.0, 7.0, 'protein', 'dinner', 'non_vegetarian', 150),
    ('Chicken Tikka', 180, 25.0, 3.0, 8.0, 'protein', 'dinner', 'non_vegetarian', 150),
    ('Keema (Minced Meat)', 220, 18.0, 4.0, 15.0, 'protein', 'dinner', 'non_vegetarian', 150),

    # Protein - Veg
    ('Dal (Toor)', 343, 22.0, 57.0, 1.5, 'legumes', 'lunch', 'vegetarian', 150),
    ('Dal (Moong)', 347, 24.0, 59.0, 1.2, 'legumes', 'lunch', 'vegetarian', 150),
    ('Dal (Masoor)', 352, 25.0, 60.0, 1.1, 'legumes', 'lunch', 'vegetarian', 150),
    ('Rajma (Kidney Beans)', 333, 24.0, 60.0, 0.8, 'legumes', 'lunch', 'vegetarian', 150),
    ('Chole (Chickpeas)', 364, 19.0, 61.0, 6.0, 'legumes', 'lunch', 'vegetarian', 150),
    ('Soy Chunks', 345, 52.0, 33.0, 0.5, 'protein', 'lunch', 'vegetarian', 50),
    ('Tofu', 76, 8.0, 1.9, 4.8, 'protein', 'lunch', 'vegan', 100),
    ('Sprouts (Moong)', 30, 3.0, 5.0, 0.2, 'legumes', 'morning_snack', 'vegan', 100),
    ('Sprouts Salad', 45, 4.0, 7.0, 0.5, 'legumes', 'morning_snack', 'vegan', 150),
    ('Chana Dal', 360, 22.0, 58.0, 5.0, 'legumes', 'lunch', 'vegetarian', 150),
    ('Black Chana', 364, 19.0, 61.0, 6.0, 'legumes', 'lunch', 'vegetarian', 150),
    ('Hummus', 166, 8.0, 14.0, 10.0, 'legumes', 'evening_snack', 'vegan', 50),

    # Vegetables
    ('Mixed Vegetable Sabzi', 65, 2.5, 10.0, 2.0, 'vegetables', 'lunch', 'vegetarian', 150),
    ('Palak Paneer', 120, 8.0, 6.0, 8.0, 'vegetables', 'lunch', 'vegetarian', 200),
    ('Baingan Bharta', 80, 2.0, 10.0, 4.0, 'vegetables', 'lunch', 'vegetarian', 150),
    ('Aloo Gobi', 90, 3.0, 12.0, 4.0, 'vegetables', 'lunch', 'vegetarian', 150),
    ('Bhindi Masala', 75, 2.5, 10.0, 3.0, 'vegetables', 'lunch', 'vegetarian', 150),
    ('Mixed Salad', 25, 1.5, 4.0, 0.3, 'vegetables', 'any', 'vegan', 150),
    ('Cucumber Salad', 15, 0.7, 3.0, 0.1, 'vegetables', 'evening_snack', 'vegan', 150),
    ('Tomato Soup', 35, 1.5, 6.0, 0.5, 'vegetables', 'dinner', 'vegan', 250),
    ('Vegetable Soup', 45, 2.0, 7.0, 1.0, 'vegetables', 'dinner', 'vegan', 250),
    ('Steamed Vegetables', 35, 2.0, 6.0, 0.3, 'vegetables', 'dinner', 'vegan', 150),
    ('Cabbage Sabzi', 40, 1.5, 7.0, 0.5, 'vegetables', 'lunch', 'vegan', 150),
    ('Carrot Sabzi', 55, 1.0, 10.0, 2.0, 'vegetables', 'lunch', 'vegan', 150),
    ('Green Beans Sabzi', 35, 2.0, 6.0, 0.3, 'vegetables', 'lunch', 'vegan', 150),
    ('Methi Thepla', 280, 8.0, 35.0, 12.0, 'grains', 'breakfast', 'vegetarian', 80),
    ('Pav Bhaji', 180, 4.0, 25.0, 8.0, 'vegetables', 'dinner', 'vegetarian', 250),

    # Fruits
    ('Banana', 89, 1.1, 23.0, 0.3, 'fruits', 'morning_snack', 'vegan', 120),
    ('Apple', 52, 0.3, 14.0, 0.2, 'fruits', 'morning_snack', 'vegan', 180),
    ('Orange', 47, 0.9, 12.0, 0.1, 'fruits', 'morning_snack', 'vegan', 150),
    ('Papaya', 43, 0.5, 11.0, 0.3, 'fruits', 'morning_snack', 'vegan', 150),
    ('Mango', 60, 0.8, 15.0, 0.4, 'fruits', 'evening_snack', 'vegan', 200),
    ('Watermelon', 30, 0.6, 8.0, 0.2, 'fruits', 'evening_snack', 'vegan', 200),
    ('Pomegranate', 83, 1.7, 19.0, 1.2, 'fruits', 'morning_snack', 'vegan', 150),
    ('Guava', 68, 2.6, 14.0, 1.0, 'fruits', 'morning_snack', 'vegan', 150),
    ('Grapes', 69, 0.7, 18.0, 0.2, 'fruits', 'evening_snack', 'vegan', 150),
    ('Pineapple', 50, 0.5, 13.0, 0.1, 'fruits', 'evening_snack', 'vegan', 150),
    ('Berries Mix', 57, 0.7, 14.0, 0.3, 'fruits', 'morning_snack', 'vegan', 100),
    ('Fruit Salad', 55, 0.8, 13.0, 0.3, 'fruits', 'evening_snack', 'vegan', 200),

    # Nuts & Seeds
    ('Almonds', 579, 21.0, 22.0, 50.0, 'nuts', 'morning_snack', 'vegan', 30),
    ('Walnuts', 654, 15.0, 14.0, 65.0, 'nuts', 'morning_snack', 'vegan', 30),
    ('Cashews', 553, 18.0, 30.0, 44.0, 'nuts', 'evening_snack', 'vegan', 30),
    ('Peanuts', 567, 26.0, 16.0, 49.0, 'nuts', 'evening_snack', 'vegan', 30),
    ('Peanut Butter', 588, 25.0, 20.0, 50.0, 'nuts', 'breakfast', 'vegan', 30),
    ('Chia Seeds', 486, 17.0, 42.0, 31.0, 'nuts', 'breakfast', 'vegan', 15),
    ('Flax Seeds', 534, 18.0, 29.0, 42.0, 'nuts', 'breakfast', 'vegan', 15),
    ('Pumpkin Seeds', 559, 30.0, 11.0, 49.0, 'nuts', 'evening_snack', 'vegan', 20),
    ('Sunflower Seeds', 584, 21.0, 20.0, 51.0, 'nuts', 'evening_snack', 'vegan', 20),
    ('Mixed Dry Fruits', 500, 10.0, 60.0, 25.0, 'nuts', 'morning_snack', 'vegan', 30),

    # Snacks
    ('Roasted Chana', 364, 19.0, 61.0, 6.0, 'snacks', 'evening_snack', 'vegan', 50),
    ('Makhana (Fox Nuts)', 347, 9.7, 77.0, 0.1, 'snacks', 'evening_snack', 'vegan', 30),
    ('Dhokla', 160, 6.0, 25.0, 4.0, 'snacks', 'evening_snack', 'vegetarian', 100),
    ('Samosa (Baked)', 262, 5.0, 30.0, 14.0, 'snacks', 'evening_snack', 'vegetarian', 80),
    ('Vada Pav', 280, 6.0, 35.0, 13.0, 'snacks', 'evening_snack', 'vegetarian', 150),
    ('Bhel Puri', 180, 4.0, 30.0, 5.0, 'snacks', 'evening_snack', 'vegetarian', 150),
    ('Poha Cutlet', 200, 5.0, 28.0, 8.0, 'snacks', 'evening_snack', 'vegetarian', 100),
    ('Energy Bar (Homemade)', 350, 10.0, 45.0, 15.0, 'snacks', 'morning_snack', 'vegetarian', 50),
    ('Trail Mix', 462, 14.0, 44.0, 29.0, 'snacks', 'morning_snack', 'vegan', 40),
    ('Khakra', 380, 10.0, 55.0, 14.0, 'snacks', 'evening_snack', 'vegetarian', 30),

    # Beverages
    ('Green Tea', 1, 0.0, 0.0, 0.0, 'beverages', 'morning_snack', 'vegan', 250),
    ('Black Coffee', 2, 0.3, 0.0, 0.0, 'beverages', 'breakfast', 'vegan', 250),
    ('Coconut Water', 19, 0.7, 3.7, 0.2, 'beverages', 'morning_snack', 'vegan', 250),
    ('Fresh Orange Juice', 45, 0.7, 10.0, 0.2, 'beverages', 'morning_snack', 'vegan', 250),
    ('Smoothie (Fruit)', 80, 2.0, 18.0, 0.5, 'beverages', 'breakfast', 'vegan', 300),
    ('Protein Shake (Homemade)', 120, 15.0, 10.0, 3.0, 'beverages', 'morning_snack', 'vegetarian', 300),
    ('Turmeric Milk', 70, 3.5, 6.0, 3.5, 'beverages', 'dinner', 'vegetarian', 250),
    ('Herbal Tea', 2, 0.0, 0.5, 0.0, 'beverages', 'evening_snack', 'vegan', 250),

    # Additional Indian dishes
    ('Misal Pav', 250, 10.0, 30.0, 10.0, 'legumes', 'breakfast', 'vegetarian', 250),
    ('Medu Vada', 250, 8.0, 30.0, 12.0, 'grains', 'breakfast', 'vegetarian', 80),
    ('Pesarattu', 180, 8.0, 25.0, 5.0, 'grains', 'breakfast', 'vegetarian', 150),
    ('Thepla', 280, 8.0, 35.0, 12.0, 'grains', 'breakfast', 'vegetarian', 80),
    ('Puri', 350, 8.0, 45.0, 15.0, 'grains', 'breakfast', 'vegetarian', 60),
    ('Sabudana Khichdi', 200, 2.0, 40.0, 4.0, 'grains', 'breakfast', 'vegetarian', 200),
    ('Vermicelli Upma', 180, 4.0, 35.0, 3.0, 'grains', 'breakfast', 'vegetarian', 200),
    ('Besan Chilla', 180, 10.0, 15.0, 8.0, 'grains', 'breakfast', 'vegetarian', 150),
    ('Moong Dal Cheela', 160, 12.0, 18.0, 4.0, 'grains', 'breakfast', 'vegetarian', 150),

    # More lunch/dinner items
    ('Jeera Rice', 150, 3.0, 28.0, 3.0, 'grains', 'lunch', 'vegetarian', 150),
    ('Lemon Rice', 140, 2.5, 27.0, 3.0, 'grains', 'lunch', 'vegetarian', 150),
    ('Curd Rice', 130, 4.0, 22.0, 3.0, 'grains', 'lunch', 'vegetarian', 200),
    ('Dal Tadka', 120, 8.0, 15.0, 4.0, 'legumes', 'lunch', 'vegetarian', 200),
    ('Dal Makhani', 150, 8.0, 18.0, 6.0, 'legumes', 'dinner', 'vegetarian', 200),
    ('Kadhi Pakora', 130, 5.0, 15.0, 6.0, 'legumes', 'lunch', 'vegetarian', 200),
    ('Sambar', 80, 4.0, 12.0, 2.0, 'legumes', 'lunch', 'vegetarian', 200),
    ('Rasam', 40, 1.5, 7.0, 0.5, 'legumes', 'lunch', 'vegetarian', 200),
    ('Avial', 90, 3.0, 10.0, 5.0, 'vegetables', 'lunch', 'vegetarian', 150),
    ('Malai Kofta', 200, 6.0, 15.0, 14.0, 'vegetables', 'dinner', 'vegetarian', 200),
    ('Shahi Paneer', 220, 12.0, 10.0, 16.0, 'vegetables', 'dinner', 'vegetarian', 200),
    ('Matar Paneer', 180, 12.0, 10.0, 12.0, 'vegetables', 'lunch', 'vegetarian', 200),
    ('Chana Masala', 150, 8.0, 20.0, 5.0, 'legumes', 'lunch', 'vegetarian', 200),
    ('Aloo Matar', 100, 3.0, 15.0, 3.0, 'vegetables', 'lunch', 'vegetarian', 150),
    ('Baigan Ka Bharta', 80, 2.0, 10.0, 4.0, 'vegetables', 'dinner', 'vegetarian', 150),

    # Non-veg additional
    ('Butter Chicken', 220, 20.0, 8.0, 13.0, 'protein', 'dinner', 'non_vegetarian', 200),
    ('Chicken Biryani', 200, 15.0, 25.0, 7.0, 'grains', 'lunch', 'non_vegetarian', 300),
    ('Egg Curry', 160, 12.0, 5.0, 10.0, 'protein', 'dinner', 'non_vegetarian', 200),
    ('Fish Fry', 180, 22.0, 5.0, 8.0, 'protein', 'dinner', 'non_vegetarian', 150),
    ('Kebab (Chicken)', 190, 25.0, 3.0, 9.0, 'protein', 'dinner', 'non_vegetarian', 150),

    # Vegan extras
    ('Vegetable Biryani', 160, 4.0, 28.0, 4.0, 'grains', 'lunch', 'vegan', 250),
    ('Coconut Chutney', 120, 2.0, 5.0, 11.0, 'snacks', 'breakfast', 'vegan', 30),
    ('Tomato Chutney', 45, 1.0, 8.0, 1.0, 'snacks', 'any', 'vegan', 30),
    ('Coconut Rice', 180, 3.0, 30.0, 6.0, 'grains', 'lunch', 'vegan', 200),
    ('Vegetable Pulao', 150, 4.0, 25.0, 4.0, 'grains', 'lunch', 'vegan', 250),
    ('Soya Curry', 130, 15.0, 10.0, 4.0, 'protein', 'dinner', 'vegan', 200),
    ('Jackfruit Curry', 95, 2.0, 18.0, 1.5, 'vegetables', 'dinner', 'vegan', 200),
    ('Mushroom Masala', 70, 4.0, 8.0, 3.0, 'vegetables', 'dinner', 'vegan', 150),
    ('Stuffed Capsicum', 80, 3.0, 12.0, 2.5, 'vegetables', 'dinner', 'vegan', 200),
    ('Baingan Ka Raita', 55, 3.0, 6.0, 2.0, 'vegetables', 'lunch', 'vegetarian', 100),

    # Global and non-oily items for broader diets
    ('Boiled Egg', 155, 13.0, 1.1, 11.0, 'protein', 'breakfast', 'non_vegetarian', 50, 'boiled'),
    ('Poached Egg', 155, 13.0, 1.1, 11.0, 'protein', 'breakfast', 'non_vegetarian', 50, 'poached'),
    ('Grilled Chicken Breast', 165, 31.0, 0.0, 3.6, 'protein', 'lunch', 'non_vegetarian', 150, 'grilled'),
    ('Steamed Fish', 110, 23.0, 0.0, 2.0, 'protein', 'dinner', 'non_vegetarian', 150, 'steamed'),
    ('Boiled Chickpeas', 164, 9.0, 27.0, 2.6, 'legumes', 'lunch', 'vegetarian', 100, 'boiled'),
    ('Steamed Broccoli', 35, 2.5, 7.5, 0.4, 'vegetables', 'any', 'vegan', 100, 'steamed'),
    ('Raw Vegetable Salad', 25, 1.5, 4.0, 0.2, 'vegetables', 'any', 'vegan', 150, 'raw'),
    ('Boiled Potato', 87, 2.0, 20.0, 0.1, 'vegetables', 'lunch', 'vegetarian', 150, 'boiled'),
    ('Oatmeal with Water', 68, 2.4, 12.0, 1.4, 'grains', 'breakfast', 'vegan', 200, 'boiled'),
    ('Steamed Spinach', 23, 2.9, 3.6, 0.4, 'vegetables', 'any', 'vegan', 100, 'steamed'),
    ('Grilled Tofu', 94, 10.0, 1.9, 5.3, 'protein', 'lunch', 'vegan', 100, 'grilled'),
    ('Boiled Quinoa', 120, 4.4, 21.3, 1.9, 'grains', 'lunch', 'vegan', 150, 'boiled'),
    ('Apple Slices', 52, 0.3, 14.0, 0.2, 'fruits', 'morning_snack', 'vegan', 150, 'raw'),
    ('Banana', 89, 1.1, 23.0, 0.3, 'fruits', 'morning_snack', 'vegan', 120, 'raw'),
    ('Cucumber Sticks', 16, 0.7, 3.6, 0.1, 'vegetables', 'morning_snack', 'vegan', 150, 'raw'),
    ('Boiled Lentils', 116, 9.0, 20.0, 0.4, 'legumes', 'lunch', 'vegetarian', 150, 'boiled'),
    ('Steamed Mixed Vegetables', 40, 2.0, 8.0, 0.5, 'vegetables', 'evening_snack', 'vegan', 150, 'steamed'),
    ('Grilled Vegetable Skewers', 70, 2.0, 9.0, 1.5, 'vegetables', 'lunch', 'vegan', 150, 'grilled'),
]


class Command(BaseCommand):
    help = 'Seed the database with Indian food items and broader raw/non-oily options'

    def handle(self, *args, **options):
        created = 0
        for food_data in FOODS:
            if len(food_data) == 10:
                name, cal, prot, carb, fat, cat, meal, diet, serving, style = food_data
            else:
                name, cal, prot, carb, fat, cat, meal, diet, serving = food_data
                style = 'regular'
            _, was_created = Food.objects.get_or_create(
                name=name,
                defaults={
                    'calories': cal,
                    'protein': prot,
                    'carbs': carb,
                    'fat': fat,
                    'category': cat,
                    'meal_type': meal,
                    'diet_type': diet,
                    'preparation_style': style,
                    'serving_size_g': serving,
                }
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {created} new foods. Total: {Food.objects.count()} foods in database.'
        ))