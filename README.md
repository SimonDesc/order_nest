# Order Nest Main Project Overview 🚀📚

## Introduction 🌟

The Order Nest Main project is a web application aimed at simplifying order management.

Built with Python and modern web tech, it helps manage orders efficiently and can scale to meet growing demands.

It's been used in a small company since December 2023 and continues to evolve.

## Table of Contents 📖

- [Introduction](#introduction-)
- [Latest Updates](#latest-updates-)
- [Project Setup](#project-setup-)
- [Running the Application](#running-the-application-)
- [Features](#features-)
- [Technologies Used](#technologies-used-)
- [Contributors](#contributors-)
- [License](#license-)

## Latest Updates 🔄

### 02/2024
- **Feature:** Creation of a ticket printing option (generate a pdf). Creation of an option to send sms to the customer with default sms and/or message personalization.
- **Bug Fixes:** Sorting by creation date was not correctly performed in the dashboard.

### 02/2024
- **Feature:** Creation of a customer creation/search/consultation menu, including customer history by customer.
- **Design:** New background, minor styling tweaks, new font.
- **Bug Fixes:** The deposit now correctly deducts from the total amount of the order.
- **Small Changes:** New card order management (urgent cards are now highlighted).

### 01/2024
- **Feature:** Redesign of dashboard to categorize order status, addition of a consultation button in cards, addition of a "Down payment" field, addition of an order completed button, addition of a "payment status" column.
- **Design:** Redesign of cards.
- **Small Changes:** New background, centering of certain elements, default status "In progress", display of down payment calculation.

## Project Setup 🛠️

To get started with the project, clone the repository and install the dependencies:

```bash
git clone https://github.com/SimonDesc/order_nest
pipenv install
```

## Running the Application 🚀

Activate the virtual environment, navigate to the source directory, and start the application:

```bash
pipenv shell
cd src/
python manage.py runserver
# In a new terminal window or tab:
python manage.py tailwind start
```

## Features 🌈

- Order Management
- Client Management
- Adding products to each order
- Adding photos
- Adding sketches
- Status Management (In Progress, Invoiced, Urgent, etc.)

## Technologies Used 💻

- Django
- Tailwind CSS
- JavaScript
- jQuery
- HTMX

## Contributors ✨

- **Simon Descombes**
  - LinkedIn: [Simon](https://www.linkedin.com/in/simon-descombes/)
  - GitHub: [SimonDesc](https://github.com/SimonDesc)

- **Valentin Raillard**
  - LinkedIn: [Valentin](https://www.linkedin.com/in/valentin-ralliard/)
  - GitHub: [Pizzayolow](https://github.com/Pizzayolow)

## License 📄

This project is not licensed and is open for personal and non-commercial use. Feel free to explore and use the code as inspiration for your own projects. If you have any questions or need further clarification, please reach out.
