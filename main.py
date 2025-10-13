from app import create_app

app = create_app()

if __name__ == "__main__":
    # Debug=True auto-reloads on code changes
    app.run(debug=True)
