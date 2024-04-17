# RecipeHub


## Introduction

Welcome to RecipeHub! RecipeHub is a full-stack web application developed as the final project of ALX Software Engineering. It serves as an all-in-one solution for restaurants, providing customers with the ability to view menus, reserve tables, leave reviews, and register as members. Additionally, it includes an intra-system for seamless order management, with sessions for chefs, waiters, and cashiers.

RecipeHub is built using Flask for the backend, MySQL for the database, and HTML, Ajax, and jQuery for the frontend.

[recording.webm](https://github.com/mohammedchakir/Recipehub/assets/36488900/9781499f-c242-4ee6-8848-ff7f1a4d8943)

Visit the deployed site: [RecipeHub](https://reciphub.pythonanywhere.com/)


Check out our final project blog article: [Blog Article](https://www.blogger.com/blog/post/edit/preview/3322922446122045835/1015185131249697797)

### Authors

- [Saleh Elmouiny](https://www.linkedin.com/in/saleh-elmouiny/) [Github](https://github.com/Elmouinysaleh)
- [Mohammed Chakir](https://www.linkedin.com/in/mohammedchakir/) [Github](https://github.com/mohammedchakir)

## Technologies Used

- **Backend**: Flask
- **Frontend**: HTML, Ajax, jQuery
- **Database**: MySQL
- **Deployment**: PythonAnywhere

## Installation

To run RecipeHub locally, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/mohammedchakir/Recipehub.git
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the MySQL database and configure the connection in `app.py`.
   ## Database Setup

To set up the database for RecipeHub using phpMyAdmin and MySQL, follow these steps:

### 1. Create Database

1. Log in to phpMyAdmin.
2. Click on the "Databases" tab.
3. Enter `recipehub` as the database name and click "Create".

### 2. Import Script File

1. Select the `recipehub` database from the left sidebar.
2. Click on the "Import" tab in the top menu.
3. Choose the `recipehub.sql` script file provided in the repository.
4. Click "Go" to import the script file and create the database schema.

### 3. Update Database Configuration (Optional)

If you're using a database configuration file in your project, such as `config.py`, you may need to update it with the database connection details. However, since you're using phpMyAdmin directly, this step may not be necessary.

### 4. Run the Application

Once you've completed the import step, you're ready to run the RecipeHub application. If you're using Flask, navigate to the project directory and execute the following command:

```bash
python app.py


5. Run the Flask application:

   ```bash
   python app.py
   ```

## Features

- **View Menu**: Customers can browse the restaurant's menu and view detailed descriptions of dishes.
- **Reserve Table**: Customers can reserve tables for dining in using the reservation feature.
- **Leave Review**: Customers can leave reviews and ratings for dishes they've tried.
- **Member Registration**: Customers can register as members for access to exclusive offers and promotions.
- **Intra-System Ordering**: Streamlined order management system for chefs, waiters, and cashiers.
- **Chef Session**: Chefs can track orders and manage food preparation.
- **Waiter Session**: Waiters can receive order calls and manage table assignments.
- **Cashier Session**: Cashiers can process payments and track transactions.

## Contributing

Contributions are welcome! If you'd like to contribute to RecipeHub, please fork the repository and submit a pull request with your changes.


## Support

For any inquiries or support, please contact us at support@recipehub.com.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
