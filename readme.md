# 📒 Professional Contact Book Application

A modern contact management desktop application built using **Python**, **PyQt5**, and **Microsoft SQL Server**. This app allows users to store, update, delete, search, import, and export their contact details.

## 🚀 Features

- Add, update, and delete contacts
- Categorize contacts (Family, Friends, Work, Other)
- Search functionality
- Import/export contacts in CSV format
- Modern and user-friendly PyQt interface
- Compatible with Microsoft SQL Server and MySQL (optional)

## 🧰 Technologies Used

- Python 3.8+
- PyQt5
- Microsoft SQL Server (via `pyodbc`)
- MySQL (optional alternative via `mysql-connector-python`)

## 🗂️ Project Structure

```bash
📁 contact-book-app/
├── main.py               # Main application logic and GUI
├── database_mssql.py     # MSSQL database handler
├── create_contactbook.sql # SQL script to create database and table
├── requirements.txt      # Python dependencies
└── README.md             # Project information and instructions
```

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/phoenixmariepornstaractress/contact-book-app.git
   cd contact-book-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:
   - Run `create_contactbook.sql` in Microsoft SQL Server Management Studio

4. Launch the application:
   ```bash
   python main.py
   ```

## 🤝 Contributing

We welcome contributions from the community! ✨

To contribute:
1. Fork the repository
2. Create a new branch (`git checkout -b feature-name`)
3. Make your changes and commit them (`git commit -am 'Add new feature'`)
4. Push to your fork (`git push origin feature-name`)
5. Open a Pull Request

Please make sure your code follows our style guidelines and includes relevant documentation or comments.

## 📬 Feedback & Contact

If you have suggestions or issues, feel free to open an [issue](https://github.com/yourusername/contact-book-app/issues) or reach out via email.

---

**Made with ❤️ for productivity and learning.**
