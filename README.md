# SMART BUDGET AND INVESTMENT TRACKER
#### Video Demo:  https://youtu.be/iwchPqYWgKw
#### Description: 
Managing personal finances effectively is one of the biggest challenges in today’s world. Most individuals struggle to keep track of their incomes, expenses, and investments due to lack of a proper system. To solve this problem, I built a **Smart Budget and Investment Tracker**, a lightweight yet powerful application that helps users monitor their financial activities in an organized and intelligent manner. This project aims to make financial planning more accessible by providing a centralized platform where users can manage budgets, record transactions, analyze investments, and even look up stock market data in real time.

The system is designed with simplicity and usability in mind. It provides an intuitive dashboard that displays an overview of a user’s financial health, including total income, expenses, savings, and category-wise expense distribution. Instead of relying on manual spreadsheets or scattered notes, users can maintain all their financial data within one system.


#### Core Feature: 

##### Income and Expense Tracking
Users can add, edit, and delete their financial transactions. Each transaction is classified as either an income or an expense. This makes it easy to view monthly trends, track cash flow, and analyze spending patterns over time.

##### Interactive Dashboard
The homepage contains a dynamic dashboard that shows financial summaries using charts and tables. It gives users a clear picture of where their money is going, which helps them make smarter financial decisions.

##### Stock and Investment Lookup
One of the highlights of the system is its ability to fetch real-time stock prices. Users can search for shares and current market prices directly within the application. This bridges the gap between everyday budgeting and long-term investment planning.

##### Profile Management
Users can upload profile images that are stored in a dedicated profile folder. The application ensures that uploaded files are handled securely and linked to the correct user account.

##### File Uploads for Bulk Data Entry
For users who prefer working with spreadsheets, the system includes an upload feature. CSV or XLSX files containing financial data can be uploaded and stored in the upload folder. The application then reads and processes these files to automatically insert transactions into the database.

##### Search and Filter Functionalities
With the integrated search feature, users can look up specific records or stock prices quickly. This saves time and improves the overall user experience.


#### Technical Overview

The application follows a client-server architecture with a clean separation between frontend and backend components.

##### Frontend (HTML, CSS, JavaScript)
The user interface is designed using _HTML_ for structure, _CSS_ for styling, and _JavaScript_ for interactivity. Custom stylesheets ensure a modern, responsive look, while _JavaScript_ adds dynamic behavior such as handling events, validating forms, and updating elements without reloading the page. All these static resources are stored inside the _static_ folder, which also houses uploaded profile images.

##### Backend (Python Flask)
The server-side logic is powered by _Flask_, a lightweight _Python_ web framework. _Flask_ routes handle user requests, process inputs, and render dynamic HTML templates. It also manages sessions, ensuring a secure and personalized experience for each user.

##### Database (SQLite3)
For persistent data storage, the project uses _SQLite3_. It is lightweight, serverless, and ideal for small to medium-scale applications. All income, expense, and investment records are stored in structured tables, allowing easy retrieval and aggregation through SQL queries.

##### Templates (Jinja2)
_Flask_’s templating engine _Jinja2_ is used to render dynamic content inside _HTML_ files. All the template files are placed in the templates folder, ensuring a clean project structure.

##### Helper Functions
To keep the code modular, I created a separate file named _helpers.py_. This file contains reusable utility functions that are imported into _app.py_. By separating concerns, the codebase becomes easier to maintain and extend.

##### Requirements
The _requirements.txt_ file lists all the necessary _Python_ dependencies required to run the project. This makes deployment simpler, as users can install all the libraries with a single command.


#### Workflow

##### User Interaction
A user opens the application in their browser and interacts with the _UI_, such as entering transactions, uploading files, or searching for stock data.

##### Request Handling
The frontend sends a request to the backend via _Flask_ routes.

##### Data Processing
The backend processes the input. For example, if a new expense is entered, Flask validates the data, saves it into the _SQLite3_ database, and then updates the dashboard.

##### Response Rendering
Once processing is complete, the backend sends a response, which is rendered in the frontend as a dynamic HTML page with updated charts and tables.


#### Benefits

**User-Friendly**: Simple interface with clear navigation.

**Efficient Tracking**: Helps users stay disciplined with budgeting.

**Integrated Investments**: Combines personal finance with real-time market data.

**Scalable**: Can be extended with additional features such as recurring transactions, goal tracking, or predictive analytics.

**Portable**: Since it uses _SQLite3_, the entire system is lightweight and can run on almost any environment without complex setup.


#### Future Enhancements

Integration of APIs for cryptocurrency prices.

Machine learning–based spending prediction and savings suggestions.

Multi-user authentication with role-based access.

Mobile app version using frameworks like React Native or Flutter.


#### Conclusion

The **Smart Budget and Investment Tracker** is more than just a budgeting tool—it’s a complete financial management assistant. It combines the simplicity of expense tracking with the intelligence of stock price lookups, giving users a unique all-in-one platform to manage both short-term and long-term finances. With its modular design, lightweight architecture, and user-friendly interface, this project demonstrates how technology can simplify complex financial management tasks.