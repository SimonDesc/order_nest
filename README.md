# Order Nest Main Project Overview 🚀📚

## Introduction 🌟

The Order Nest Main project is a web application aimed at simplifying order management.

Built with Python and modern web tech, it helps manage orders efficiently and can scale to meet growing demands.

It's been used in a small company since December 2023 and continues to evolve.


![HomeView](https://ordernest2.s3.eu-north-1.amazonaws.com/order_attachments/Capture%20d%E2%80%99%C3%A9cran%202024-03-19%20%C3%A0%2014.27.16.png?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEOb%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCWV1LXdlc3QtMyJGMEQCIC7ge3IqJrnhujVdiv4Z02E2phTuMaCsYjtFZNJWhEQAAiBjRNOTMTGBZ%2Bzk8dlHnVUeUHuifMUziN0aQz5t1%2FYnjyrtAgjv%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAAaDDUzMTE5ODEwNTQwMCIMC%2F0ZS3ODDcgCLAaCKsECcbR0lNcpOtDKxJujPmF0%2FVWFlSBlNHscs47G5Gqsn2yHzDaBXsmH5nOZIYUB2YO0kmSVH1TjadT4YbgTjQKN%2BFrOtx2ENe0eGGuS312gzQJcgabz6wjJSc11fY%2B7spAbLWXrKlGcV1Z2HQDHq0MyZ7QsAyHOupCbJPFcF6CGIULjjWP6HaHKM%2F56QQ%2FQuJQPgeu37S3XRPfmWl8oOES%2FLE%2BaRfH%2BdY6K1mC58qCGVUJ756GjSQSk7TvqGkaAo7t3GneBFlUBB9TFoWVyB0BDITE3hOUAcygOT7x6y1YPsUkc3FEaIcxqm6xIATp12jj502tdLaVeVfyx9v7E1u00HxqVeB2xsBdP4FOznpF07ysJnu7AT3vIAXSYQs2vjN1GD8ZtWg3rz1CNGGtK5FlrIcJmfc4VxUIqUxahsmNs5mBSMMak5q8GOrQCcSPnUBTr7Jzn400ZiElQdpXU2z5yjkIqM70v7xhbmy47XvHmLbcbGbNtN8GeWtv3lBfTo7vjqPEdKKDgdaguPP4SuBjQEMWVrem3O1VBgVSfwQWT5FROdde%2FRpgkjYvyamr6GufIju88Ex9jqbrH48Y3SqPUKgubRUVOM8UYuQ5RtLcZWNRHg6kZCJ7E4ZmMqu4F%2BNlg6JYJkLMQcTRRTHRZdlN3tAPycYxFLnE5TouRWB5xRlRXB1X%2F1FRTfcw%2BH8zZPlRK2L7SZJChSaorwVSDe7wr8hmvMz3a%2B6NHumDE8F9jsahUQSp%2FAhUgwBEe3q71LiLnZR%2BIaBN399qkwhQrkyjA0DKt9ICw2AKO37amzRi%2FhZzCTFhMmDiT7TcVkvYhzAfLaIQmVt%2FsHKGIg905EjU%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240319T132935Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAXXLO7244C4LOWPEF%2F20240319%2Feu-north-1%2Fs3%2Faws4_request&X-Amz-Signature=df74868ad174884483bb0c8c03257d36771ef64807df4337c31fbe567c7ee5ee "Home view")


![EditView](https://ordernest2.s3.eu-north-1.amazonaws.com/order_attachments/Capture%20d%E2%80%99%C3%A9cran%202024-03-19%20%C3%A0%2014.25.02.png?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEOb%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCWV1LXdlc3QtMyJGMEQCIC7ge3IqJrnhujVdiv4Z02E2phTuMaCsYjtFZNJWhEQAAiBjRNOTMTGBZ%2Bzk8dlHnVUeUHuifMUziN0aQz5t1%2FYnjyrtAgjv%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAAaDDUzMTE5ODEwNTQwMCIMC%2F0ZS3ODDcgCLAaCKsECcbR0lNcpOtDKxJujPmF0%2FVWFlSBlNHscs47G5Gqsn2yHzDaBXsmH5nOZIYUB2YO0kmSVH1TjadT4YbgTjQKN%2BFrOtx2ENe0eGGuS312gzQJcgabz6wjJSc11fY%2B7spAbLWXrKlGcV1Z2HQDHq0MyZ7QsAyHOupCbJPFcF6CGIULjjWP6HaHKM%2F56QQ%2FQuJQPgeu37S3XRPfmWl8oOES%2FLE%2BaRfH%2BdY6K1mC58qCGVUJ756GjSQSk7TvqGkaAo7t3GneBFlUBB9TFoWVyB0BDITE3hOUAcygOT7x6y1YPsUkc3FEaIcxqm6xIATp12jj502tdLaVeVfyx9v7E1u00HxqVeB2xsBdP4FOznpF07ysJnu7AT3vIAXSYQs2vjN1GD8ZtWg3rz1CNGGtK5FlrIcJmfc4VxUIqUxahsmNs5mBSMMak5q8GOrQCcSPnUBTr7Jzn400ZiElQdpXU2z5yjkIqM70v7xhbmy47XvHmLbcbGbNtN8GeWtv3lBfTo7vjqPEdKKDgdaguPP4SuBjQEMWVrem3O1VBgVSfwQWT5FROdde%2FRpgkjYvyamr6GufIju88Ex9jqbrH48Y3SqPUKgubRUVOM8UYuQ5RtLcZWNRHg6kZCJ7E4ZmMqu4F%2BNlg6JYJkLMQcTRRTHRZdlN3tAPycYxFLnE5TouRWB5xRlRXB1X%2F1FRTfcw%2BH8zZPlRK2L7SZJChSaorwVSDe7wr8hmvMz3a%2B6NHumDE8F9jsahUQSp%2FAhUgwBEe3q71LiLnZR%2BIaBN399qkwhQrkyjA0DKt9ICw2AKO37amzRi%2FhZzCTFhMmDiT7TcVkvYhzAfLaIQmVt%2FsHKGIg905EjU%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240319T132552Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAXXLO7244C4LOWPEF%2F20240319%2Feu-north-1%2Fs3%2Faws4_request&X-Amz-Signature=732e2fe8aa0f4ca73198bb63581447536e32832507f037d09545a217bea0c233 "Edit order view")


![EditView2](https://ordernest2.s3.eu-north-1.amazonaws.com/order_attachments/Capture%20d%E2%80%99%C3%A9cran%202024-03-19%20%C3%A0%2014.32.08.png?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEOb%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCWV1LXdlc3QtMyJGMEQCIC7ge3IqJrnhujVdiv4Z02E2phTuMaCsYjtFZNJWhEQAAiBjRNOTMTGBZ%2Bzk8dlHnVUeUHuifMUziN0aQz5t1%2FYnjyrtAgjv%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAAaDDUzMTE5ODEwNTQwMCIMC%2F0ZS3ODDcgCLAaCKsECcbR0lNcpOtDKxJujPmF0%2FVWFlSBlNHscs47G5Gqsn2yHzDaBXsmH5nOZIYUB2YO0kmSVH1TjadT4YbgTjQKN%2BFrOtx2ENe0eGGuS312gzQJcgabz6wjJSc11fY%2B7spAbLWXrKlGcV1Z2HQDHq0MyZ7QsAyHOupCbJPFcF6CGIULjjWP6HaHKM%2F56QQ%2FQuJQPgeu37S3XRPfmWl8oOES%2FLE%2BaRfH%2BdY6K1mC58qCGVUJ756GjSQSk7TvqGkaAo7t3GneBFlUBB9TFoWVyB0BDITE3hOUAcygOT7x6y1YPsUkc3FEaIcxqm6xIATp12jj502tdLaVeVfyx9v7E1u00HxqVeB2xsBdP4FOznpF07ysJnu7AT3vIAXSYQs2vjN1GD8ZtWg3rz1CNGGtK5FlrIcJmfc4VxUIqUxahsmNs5mBSMMak5q8GOrQCcSPnUBTr7Jzn400ZiElQdpXU2z5yjkIqM70v7xhbmy47XvHmLbcbGbNtN8GeWtv3lBfTo7vjqPEdKKDgdaguPP4SuBjQEMWVrem3O1VBgVSfwQWT5FROdde%2FRpgkjYvyamr6GufIju88Ex9jqbrH48Y3SqPUKgubRUVOM8UYuQ5RtLcZWNRHg6kZCJ7E4ZmMqu4F%2BNlg6JYJkLMQcTRRTHRZdlN3tAPycYxFLnE5TouRWB5xRlRXB1X%2F1FRTfcw%2BH8zZPlRK2L7SZJChSaorwVSDe7wr8hmvMz3a%2B6NHumDE8F9jsahUQSp%2FAhUgwBEe3q71LiLnZR%2BIaBN399qkwhQrkyjA0DKt9ICw2AKO37amzRi%2FhZzCTFhMmDiT7TcVkvYhzAfLaIQmVt%2FsHKGIg905EjU%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240319T133259Z&X-Amz-SignedHeaders=host&X-Amz-Expires=299&X-Amz-Credential=ASIAXXLO7244C4LOWPEF%2F20240319%2Feu-north-1%2Fs3%2Faws4_request&X-Amz-Signature=4a134b6b56a9bb13d51f9d93d17b6dd95646c1c46614232357e24f7084a52349 "Edit order view Picture and Products")


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

### 03/2024
- 🎨**Design:** Changes to the navbar -> now in vertical for aesthetic and better visualization.
- 🔧**Small Changes:** Ticket printing now have prices and date.

### 02/2024 (2)
- 🌟**Features:** Creation of a ticket printing option (generate a pdf). Creation of an option to send sms to the customer with default sms and/or message personalization.
- 🐛**Bug Fixes:** Sorting by creation date was not correctly performed in the dashboard.
- 🔧**Small Changes:** New access to customer form from the order page.

### 02/2024 (1)
- 🌟**Features:** Creation of a customer creation/search/consultation menu, including customer history by customer.
- 🎨**Design:** New background, minor styling tweaks, new font.
- 🐛**Bug Fixes:** The deposit now correctly deducts from the total amount of the order.
- 🔧**Small Changes:** New card order management (urgent cards are now highlighted).

### 01/2024
- 🌟**Features:** Redesign of dashboard to categorize order status, addition of a consultation button in cards, addition of a "Down payment" field, addition of an order completed button, addition of a "payment status" column.
- 🎨**Design:** Redesign of cards.
- 🔧**Small Changes:** New background, centering of certain elements, default status "In progress", display of down payment calculation.

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
- Printing system
- Automated SMS to customer

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
