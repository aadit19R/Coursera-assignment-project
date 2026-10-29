# QuickBite ER diagram

`er_diagram.png` is the completed high-resolution image, embedded in the notebook
and PDF report. It follows the reference's black-and-white rectangular entity
style. The image shows primary and foreign keys; Part 2 lists every attribute.

The labels show the following business relationships:

- Customers 1 -> 0..many Orders
- Restaurants 1 -> 0..many MenuItems
- Restaurants 1 -> 0..many Orders
- DeliveryAgents 1 -> 0..many Orders
- Orders 1 -> 1..many OrderItems (business rule: each order has items)
- MenuItems 1 -> 0..many OrderItems
- Orders 1 -> 1 Payments (business rule: each order has one payment)
- Orders 1 -> 0..1 Reviews
- Customers 1 -> 0..many Reviews

UNIQUE on Payments.order_id and Reviews.order_id limits each to one record per
order. Foreign keys alone do not enforce that every order has a payment/item;
the inserted dataset and verification establish those business rules.

If you later choose an online editor, import the MySQL DDL below and export a
replacement PNG as `er_diagram.png`. Rebuild the PDF with:

```sh
python3 tools/build_report.py
```

The report builder embeds that image automatically. The supplied diagram was
generated locally with `python3 tools/make_er_diagram.py`.

```sql
CREATE TABLE Customers (
        customer_id INT PRIMARY KEY,
        customer_name VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        phone VARCHAR(20) NOT NULL, city VARCHAR(100) NOT NULL,
        join_date DATE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE Restaurants (
        restaurant_id INT PRIMARY KEY,
        restaurant_name VARCHAR(100) NOT NULL,
        city VARCHAR(100) NOT NULL, cuisine_type VARCHAR(100) NOT NULL,
        avg_rating DECIMAL(3,2) NOT NULL CHECK (avg_rating BETWEEN 0 AND 5)
) ENGINE=InnoDB;

CREATE TABLE MenuItems (
        item_id INT PRIMARY KEY, restaurant_id INT NOT NULL,
        item_name VARCHAR(100) NOT NULL,
        category VARCHAR(20) NOT NULL CHECK (category IN ('Veg', 'Non-Veg')),
        price DECIMAL(10,2) NOT NULL CHECK (price > 0),
        FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id)
) ENGINE=InnoDB;

CREATE TABLE DeliveryAgents (
        agent_id INT PRIMARY KEY, agent_name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) NOT NULL, vehicle_type VARCHAR(100) NOT NULL,
        city VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE Orders (
        order_id INT PRIMARY KEY, customer_id INT NOT NULL,
        restaurant_id INT NOT NULL, agent_id INT NOT NULL,
        order_date DATETIME NOT NULL,
        order_status VARCHAR(20) NOT NULL
            CHECK (order_status IN ('Placed', 'Delivered', 'Cancelled')),
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
        FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id),
        FOREIGN KEY (agent_id) REFERENCES DeliveryAgents(agent_id)
) ENGINE=InnoDB;

CREATE TABLE OrderItems (
        order_item_id INT PRIMARY KEY, order_id INT NOT NULL,
        item_id INT NOT NULL, quantity INT NOT NULL CHECK (quantity > 0),
        UNIQUE (order_id, item_id),
        FOREIGN KEY (order_id) REFERENCES Orders(order_id),
        FOREIGN KEY (item_id) REFERENCES MenuItems(item_id)
) ENGINE=InnoDB;

CREATE TABLE Payments (
        payment_id INT PRIMARY KEY, order_id INT NOT NULL UNIQUE,
        payment_mode VARCHAR(20) NOT NULL
            CHECK (payment_mode IN ('UPI', 'Card', 'Cash', 'Wallet')),
        amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
        payment_status VARCHAR(20) NOT NULL
            CHECK (payment_status IN ('Success', 'Failed')),
        FOREIGN KEY (order_id) REFERENCES Orders(order_id)
) ENGINE=InnoDB;

CREATE TABLE Reviews (
        review_id INT PRIMARY KEY, order_id INT NOT NULL UNIQUE,
        customer_id INT NOT NULL,
        rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5), comments TEXT,
        FOREIGN KEY (order_id) REFERENCES Orders(order_id),
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
) ENGINE=InnoDB;
```
