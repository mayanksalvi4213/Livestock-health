import sqlite3

# Database path
DB_PATH = 'agrihealth.db'

def check_db():
    """Check the database contents"""
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check disease_outbreak table
    cursor.execute("SELECT COUNT(*) FROM disease_outbreak")
    outbreak_count = cursor.fetchone()[0]
    print(f"Disease outbreaks: {outbreak_count}")
    
    if outbreak_count > 0:
        cursor.execute("SELECT disease_name, district, state, severity, is_active FROM disease_outbreak LIMIT 5")
        print("\nSample disease outbreaks:")
        for row in cursor.fetchall():
            disease, district, state, severity, is_active = row
            print(f"- {disease} in {district}, {state} (Severity: {severity}, Active: {'Yes' if is_active else 'No'})")
    
    # Check veterinary_service table
    cursor.execute("SELECT COUNT(*) FROM veterinary_service")
    vet_count = cursor.fetchone()[0]
    print(f"\nVeterinary services: {vet_count}")
    
    if vet_count > 0:
        cursor.execute("SELECT name, district, state, specialization FROM veterinary_service LIMIT 5")
        print("\nSample veterinary services:")
        for row in cursor.fetchall():
            name, district, state, specialization = row
            print(f"- {name} in {district}, {state} (Specialization: {specialization})")
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    check_db() 