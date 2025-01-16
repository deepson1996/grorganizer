# GrOrganizer
#### Video Demo:  <URL HERE>

#### Description:

GrOrganizer is a comprehensive web-based application designed to simplify the management of grocery lists, budgets, and related tasks. With features like category and place management, analytics, and shared grocery reports, the application helps users efficiently organize their grocery shopping while tracking expenditures and budgets.

---

#### Core Features
- **Groceries Dashboard**: View and manage all grocery items in one place.
- **Categories**: Organize grocery items into user-defined categories for better management.
- **Places**: Track where items were purchased or where they will be bought.
- **Contacts**: Manage and store contacts for sharing grocery lists.
- **Shared Groceries**: Share grocery lists with other users for collaborative management.

#### Reports and Analytics
- **Grocery Report**: Generate detailed reports on groceries, including spending and shared lists.
- **Analytics**: Visualize budget vs. expenditure trends using interactive charts.

#### Additional Features
- **Responsive Sidebar Navigation**: Intuitive navigation to quickly access all sections of the application.
- **User Management**: Displays the logged-in user’s name in the footer for easy identification.

---

### Technologies Used

#### Frontend
- **HTML5**, **CSS3**, **JavaScript**
- **Font Awesome** for icons
- **Chart.js** for creating budget vs. expenditure charts

#### Backend
- **Flask**: A lightweight Python web framework for building the backend API.
- **cs50 SQL**: ORM for database management and queries.

#### Database
- **SQLite**: Lightweight database for storing user data, grocery details, categories, places, and shared lists.

#### Deployment
- Deployed on a local server.


#### File Structure

```
project-root/
|-- static/
|   |-- css/      # Stylesheets
|   |-- js/       # JavaScript files (including Chart.js integrations)
|-- templates/    # HTML templates for the application
|-- app.py        # Main Flask application
|-- models.py     # Database models
|-- routes.py     # Application routes and API endpoints
|-- readme.md     # Project documentation
```

---

#### How to Run the Project

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/grocery-organizer.git
   cd grocery-organizer
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Run the application:
   ```bash
   flask run
   ```

6. Open the application in your browser:
   ```
   http://127.0.0.1:5000
   ```

---

#### Future Enhancements
- **Notifications**: Reminders for upcoming grocery needs or expiring items.
- **Mobile App Integration**: Dedicated mobile app for on-the-go management.
- **AI Suggestions**: Smart suggestions for items based on purchase history.
- **Multi-Currency Support**: Support for tracking groceries in various currencies.

---
