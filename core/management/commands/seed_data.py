"""Management command to seed database with demo data."""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from references.models import Client, CargoType, FuelNorm
from transport.models import Vehicle, Driver, VehicleType, VehicleStatus, TripLog
from orders.models import Order, OrderStatus, OrderStatusLog

User = get_user_model()


class Command(BaseCommand):
    help = "Заполнить БД демо-данными для разработки"

    def add_arguments(self, parser):
        parser.add_argument("--orders", type=int, default=30, help="Количество заказов")
        parser.add_argument("--vehicles", type=int, default=10, help="Количество ТС")
        parser.add_argument("--drivers", type=int, default=8, help="Количество водителей")
        parser.add_argument("--clients", type=int, default=5, help="Количество клиентов")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Начинаю заполнение БД..."))

        # Create users
        self._create_users()

        # Create references
        clients = self._create_clients(options["clients"])
        cargo_types = self._create_cargo_types()
        fuel_norms = self._create_fuel_norms()

        # Create transport
        vehicles = self._create_vehicles(options["vehicles"])
        drivers = self._create_drivers(options["drivers"], vehicles)

        # Create orders
        self._create_orders(options["orders"], clients, cargo_types, vehicles, drivers)

        # Create routes
        orders = list(Order.objects.all())
        self._create_routes(vehicles, drivers, orders)

        self.stdout.write(self.style.SUCCESS("✓ БД заполнена демо-данными!"))
        self.stdout.write(self.style.WARNING("Логин: admin / Пароль: admin"))

    def _create_users(self):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@logistic365.ru", "admin", role="admin")
            self.stdout.write("  ✓ Создан суперпользователь admin/admin")

        roles = ["dispatcher", "driver", "accountant"]
        for role in roles:
            if not User.objects.filter(username=role).exists():
                User.objects.create_user(role, f"{role}@logistic365.ru", role, role=role)
                self.stdout.write(f"  ✓ Создан пользователь {role}/{role}")

    def _create_clients(self, count):
        if Client.objects.exists():
            return list(Client.objects.all()[:count])

        names = [
            "ООО «ТрансЛогистик»",
            "ЗАО «СибГруз»",
            "ИП Иванов А.А.",
            "ООО «ФастДеливери»",
            "АО «ДальниеПеревозки»",
            "ООО «КаргоЭкспресс»",
            "ИП Петров В.В.",
        ]
        clients = []
        for i in range(min(count, len(names))):
            c = Client.objects.create(
                name=names[i],
                inn=f"{random.randint(1000000000, 9999999999)}",
                legal_address=f"г. Москва, ул. Примерная, д. {i + 1}",
                contact_person=f"Контакт {i + 1}",
                contact_phone=f"+7 (900) {i:03d}-{i:03d}-{i:03d}",
                contract_number=f"ДГ-{2024}-{i + 1:03d}",
                contract_date=timezone.now().date() - timedelta(days=random.randint(30, 365)),
            )
            clients.append(c)
        self.stdout.write(f"  ✓ Создано {len(clients)} клиентов")
        return clients

    def _create_cargo_types(self):
        if CargoType.objects.exists():
            return list(CargoType.objects.all())

        types_data = [
            ("Генеральный груз", 0),
            ("Скоропортящийся", 0),
            ("Опасный (класс 3)", 3),
            ("Неопасный наливной", 0),
            ("Тяжеловесный", 0),
        ]
        cargo_types = []
        for name, hazard in types_data:
            ct = CargoType.objects.create(name=name, hazard_class=hazard)
            cargo_types.append(ct)
        self.stdout.write(f"  ✓ Создано {len(cargo_types)} типов грузов")
        return cargo_types

    def _create_fuel_norms(self):
        if FuelNorm.objects.exists():
            return list(FuelNorm.objects.all())

        norms = [
            ("Фургон", 14.0, 11.0, 2.0),
            ("Рефрижератор", 18.0, 14.0, 3.0),
            ("Цистерна", 22.0, 17.0, 3.5),
            ("Бортовой", 16.0, 13.0, 2.5),
        ]
        result = []
        for vtype, city, highway, winter in norms:
            fn = FuelNorm.objects.create(
                vehicle_type=vtype,
                consumption_city=city,
                consumption_highway=highway,
                consumption_winter=winter,
                valid_from=timezone.now().date().replace(month=1, day=1),
            )
            result.append(fn)
        self.stdout.write(f"  ✓ Создано {len(result)} нормативов топлива")
        return result

    def _create_vehicles(self, count):
        if Vehicle.objects.exists():
            return list(Vehicle.objects.all()[:count])

        brands = ["КамАЗ", "ГАЗель", "MAN", "Volvo", "Scania", "Mercedes", "Iveko", "DAF"]
        vtypes = list(VehicleType.values)
        statuses = list(VehicleStatus.values)

        vehicles = []
        for i in range(count):
            v = Vehicle.objects.create(
                plate_number=f"А{i + 1:03d}АА77",
                vehicle_type=random.choice(vtypes),
                brand=random.choice(brands),
                model=f"Model-{random.randint(100, 999)}",
                capacity_kg=random.choice([1500, 3000, 5000, 10000, 20000]),
                volume_m3=random.choice([10, 20, 36, 60, 92]),
                current_mileage=random.randint(10000, 500000),
                fuel_consumption=random.randint(12, 25),
                next_maintenance=timezone.now().date() + timedelta(days=random.randint(1, 90)),
                status=random.choice(statuses),
            )
            vehicles.append(v)
        self.stdout.write(f"  ✓ Создано {len(vehicles)} ТС")
        return vehicles

    def _create_drivers(self, count, vehicles):
        if Driver.objects.exists():
            return list(Driver.objects.all()[:count])

        first_names = ["Александр", "Михаил", "Дмитрий", "Сергей", "Андрей", "Николай", "Иван", "Пётр"]
        last_names = ["Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов", "Михайлов", "Новиков"]

        drivers = []
        for i in range(count):
            d = Driver.objects.create(
                last_name=last_names[i % len(last_names)],
                first_name=first_names[i % len(first_names)],
                patronymic="Иванович" if i % 2 == 0 else "",
                phone=f"+7 (900) {i:03d}-{i:03d}-{i:03d}",
                license_number=f"77{i + 1:04d}{random.randint(10000, 99999)}",
                license_category=random.choice(["B", "C", "CE"]),
                medical_exam_date=timezone.now().date() - timedelta(days=random.randint(10, 365)),
                vehicle=random.choice(vehicles) if vehicles else None,
            )
            drivers.append(d)
        self.stdout.write(f"  ✓ Создано {len(drivers)} водителей")
        return drivers

    def _create_orders(self, count, clients, cargo_types, vehicles, drivers):
        if Order.objects.exists():
            self.stdout.write("  ⏭ Заказы уже существуют, пропускаю")
            return

        cargo_names = [
            "Электроника", "Продукты питания", "Стройматериалы",
            "Мебель", "Бытовая техника", "Одежда", "Книги",
            "Автозапчасти", "Химикаты", "Металлопрокат",
        ]
        cities = [
            "г. Москва", "г. Санкт-Петербург", "г. Казань",
            "г. Новосибирск", "г. Екатеринбург", "г. Нижний Новгород",
            "г. Самара", "г. Ростов-на-Дону", "г. Уфа", "г. Красноярск",
        ]
        statuses = list(OrderStatus.values)
        # Weight orders toward active statuses
        status_weights = [2, 3, 3, 4, 3, 2, 5, 1]  # more completed, more in_transit

        admin = User.objects.filter(role="admin").first()

        for i in range(count):
            loading_dt = timezone.now() - timedelta(days=random.randint(0, 30))
            delivery_dt = loading_dt + timedelta(days=random.randint(1, 7))

            status = random.choices(statuses, weights=status_weights, k=1)[0]

            client = random.choice(clients) if clients else None
            if not client:
                continue

            order = Order.objects.create(
                client=client,
                cargo_name=random.choice(cargo_names),
                cargo_type=random.choice(cargo_types) if cargo_types else None,
                cargo_weight_kg=round(random.uniform(100, 20000), 2),
                cargo_volume_m3=round(random.uniform(1, 90), 2),
                hazard_class=random.choice([0, 0, 0, 3, 0]),
                loading_address=f"{random.choice(cities)}, ул. Погрузочная, д. {random.randint(1, 50)}",
                unloading_address=f"{random.choice(cities)}, ул. Разгрузочная, д. {random.randint(1, 50)}",
                loading_datetime=loading_dt,
                required_delivery_datetime=delivery_dt,
                status=status,
                vehicle=random.choice(vehicles) if vehicles and status != OrderStatus.DRAFT else None,
                driver=random.choice(drivers) if drivers and status not in (OrderStatus.DRAFT, OrderStatus.CANCELLED) else None,
                created_by=admin,
            )

            # Create status log
            OrderStatusLog.objects.create(
                order=order,
                old_status="",
                new_status=status,
                comment="Создан при заполнении демо-данными",
                changed_by=admin,
            )

        self.stdout.write(f"  ✓ Создано {count} заказов")

    def _create_routes(self, vehicles, drivers, orders):
        from routes.models import Route, RouteStatus, Waypoint

        if Route.objects.exists():
            self.stdout.write("  ⏭ Маршруты уже существуют, пропускаю")
            return

        route_names = [
            "Москва — Санкт-Петербург",
            "Москва — Казань",
            "Москва — Нижний Новгород",
            "Екатеринбург — Новосибирск",
            "Ростов-на-Дону — Самара",
        ]
        statuses = list(RouteStatus.values)

        routes_created = 0
        for i, name in enumerate(route_names):
            vehicle = vehicles[i % len(vehicles)]
            driver = drivers[i % len(drivers)]

            # Выбираем 1-3 случайных заказа
            num_orders = random.randint(1, 3)
            route_orders = random.sample(list(orders), min(num_orders, len(orders)))

            dep_dt = timezone.now() + timedelta(days=i + 1, hours=random.randint(0, 12))

            route = Route.objects.create(
                name=name,
                status=random.choice(statuses),
                vehicle=vehicle,
                driver=driver,
                departure_datetime=dep_dt,
                created_by=User.objects.filter(role="admin").first(),
            )

            # Создаём точки из заказов
            for order in route_orders:
                route.add_waypoint_from_order(order)

            # Авторасставить координаты
            route.auto_add_geocodes()
            route.calculate_distance_and_time()
            routes_created += 1

        self.stdout.write(f"  ✓ Создано {routes_created} маршрутов")
