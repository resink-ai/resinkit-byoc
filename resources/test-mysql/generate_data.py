#!/usr/bin/env python3
"""
Generates data for the MySQL database.

> pip install mysql-connector-python faker
> MYSQL_RESINKIT_PASSWORD=resinkit_mysql_password MYSQL_RESINKIT_USER=resinkit MYSQL_RESINKIT_DATABASE=mydatabase MYSQL_TCP_PORT=3306 MYSQL_HOST=localhost python3 resources/test-mysql/generate_data.py

"""

from os import system
import os
import mysql.connector
from mysql.connector import Error
from faker import Faker
import random
from datetime import datetime, timedelta
import json
import uuid

fake = Faker()

# Database configuration
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_RESINKIT_USER", "resinkit"),
    "password": os.environ.get("MYSQL_RESINKIT_PASSWORD", "resinkit_mysql_password"),
    "database": os.environ.get("MYSQL_RESINKIT_DATABASE", "mydatabase"),
    "port": int(os.environ.get("MYSQL_TCP_PORT", 3306)),
}


# Table generators
def generate_user():
    return {
        "id": str(uuid.uuid4()),
        "name": fake.name(),
        "email": fake.email(),
        "emailVerified": fake.date_time_this_year(),
        "password": fake.password(),
        "image": fake.image_url(),
        "createdAt": fake.date_time_this_year(),
        "updatedAt": fake.date_time_this_year(),
        "invalid_login_attempts": random.randint(0, 5),
        "lockedAt": fake.date_time_this_year() if random.random() < 0.1 else None,
    }


def generate_team():
    return {
        "id": str(uuid.uuid4()),
        "name": fake.company(),
        "slug": fake.slug(),
        "domain": fake.domain_name(),
        "defaultRole": random.choice(["ADMIN", "OWNER", "MEMBER"]),
        "billingId": str(uuid.uuid4()),
        "billingProvider": random.choice(["stripe", "paypal"]),
        "createdAt": fake.date_time_this_year(),
        "updatedAt": fake.date_time_this_year(),
    }


def generate_team_member(team_id, user_id):
    return {
        "id": str(uuid.uuid4()),
        "teamId": team_id,
        "userId": user_id,
        "role": random.choice(["ADMIN", "OWNER", "MEMBER"]),
        "createdAt": fake.date_time_this_year(),
        "updatedAt": fake.date_time_this_year(),
    }


def generate_invitation(team_id, invited_by):
    return {
        "id": str(uuid.uuid4()),
        "teamId": team_id,
        "email": fake.email(),
        "role": random.choice(["ADMIN", "OWNER", "MEMBER"]),
        "token": fake.uuid4(),
        "expires": fake.future_datetime(),
        "invitedBy": invited_by,
        "createdAt": fake.date_time_this_year(),
        "updatedAt": fake.date_time_this_year(),
        "sentViaEmail": random.choice([True, False]),
        # Convert list to JSON
        "allowedDomains": json.dumps(
            [fake.domain_name() for _ in range(random.randint(0, 3))]
        ),
    }


def generate_api_key(team_id):
    return {
        "id": str(uuid.uuid4()),
        "name": fake.word(),
        "teamId": team_id,
        "hashedKey": fake.sha256(),
        "createdAt": fake.date_time_this_year(),
        "updatedAt": fake.date_time_this_year(),
        "expiresAt": fake.future_datetime(),
        "lastUsedAt": fake.date_time_this_year(),
    }


def generate_subscription():
    return {
        "id": str(uuid.uuid4()),
        "customerId": str(uuid.uuid4()),
        "priceId": str(uuid.uuid4()),
        "active": random.choice([True, False]),
        "startDate": fake.date_time_this_year(),
        "endDate": fake.future_datetime(),
        "cancelAt": fake.future_datetime() if random.random() < 0.2 else None,
        "createdAt": fake.date_time_this_year(),
        "updatedAt": fake.date_time_this_year(),
    }


def generate_service():
    return {
        "id": str(uuid.uuid4()),
        "description": fake.text(),
        "features": [fake.word() for _ in range(random.randint(1, 5))],
        "image": fake.image_url(),
        "name": fake.company(),
        "created": fake.date_time_this_year(),
        "createdAt": fake.date_time_this_year(),
        "updatedAt": fake.date_time_this_year(),
    }


def generate_price(service_id):
    return {
        "id": str(uuid.uuid4()),
        "billingScheme": random.choice(["per_unit", "tiered"]),
        "currency": fake.currency_code(),
        "serviceId": service_id,
        "amount": random.randint(100, 10000),
        "metadata": json.dumps({"key": fake.word()}),
        "type": random.choice(["one_time", "recurring"]),
        "created": fake.date_time_this_year(),
    }


def generate_data_connection_config(team_id):
    return {
        "id": str(uuid.uuid4()),
        "ownerTeamId": team_id,
        "name": fake.word(),
        "type": random.choice(["mysql", "postgresql", "mongodb"]),
        "details": json.dumps(
            {
                "host": fake.ipv4(),
                "port": random.randint(1000, 9999),
                "username": fake.user_name(),
                "password": fake.password(),
            }
        ),
        "createdBy": str(uuid.uuid4()),
        "updatedBy": str(uuid.uuid4()),
        "updatedAt": fake.date_time_this_year(),
    }


def generate_flink_cdc_config(team_id, source_conn_id, sink_conn_id):
    return {
        "id": str(uuid.uuid4()),
        "ownerTeamId": team_id,
        "name": fake.word(),
        "sourceConnId": source_conn_id,
        "sourceTables": ",".join([fake.word() for _ in range(random.randint(1, 3))]),
        "sinkConnId": sink_conn_id,
        "transform": json.dumps({"operation": "transform_data"}),
        "route": json.dumps({"path": "/data/route"}),
        "pipeline": json.dumps({"steps": ["extract", "transform", "load"]}),
        "createdBy": str(uuid.uuid4()),
        "updatedBy": str(uuid.uuid4()),
        "updatedAt": fake.date_time_this_year(),
    }


# Database operations


def connect_to_database():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
    return None


def insert_data(connection, table_name, data):
    try:
        cursor = connection.cursor()
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"

        # Convert lists/dicts to JSON and prepare the final values
        final_values = [
            json.dumps(value) if isinstance(value, (list, dict)) else value
            for value in data.values()
        ]

        # Print the SQL query and the actual values being inserted
        print(f"Executing SQL: {query}")
        print(f"With values: {final_values}")

        # Execute the query
        cursor.execute(query, final_values)
        connection.commit()
    except Error as e:
        print(f"Error inserting data into {table_name}: {e}")


# Main execution


def main():
    connection = connect_to_database()
    if not connection:
        return

    # Generate and insert data
    num_users = 10
    num_teams = 5

    users = [generate_user() for _ in range(num_users)]
    teams = [generate_team() for _ in range(num_teams)]

    for user in users:
        insert_data(connection, "User", user)

    for team in teams:
        insert_data(connection, "Team", team)

    for team in teams:
        for _ in range(random.randint(1, 3)):
            user = random.choice(users)
            team_member = generate_team_member(team["id"], user["id"])
            insert_data(connection, "TeamMember", team_member)

        for _ in range(random.randint(0, 2)):
            invitation = generate_invitation(team["id"], random.choice(users)["id"])
            insert_data(connection, "Invitation", invitation)

        for _ in range(random.randint(1, 3)):
            api_key = generate_api_key(team["id"])
            insert_data(connection, "ApiKey", api_key)

    for _ in range(num_teams * 2):
        subscription = generate_subscription()
        insert_data(connection, "Subscription", subscription)

    services = [generate_service() for _ in range(5)]
    for service in services:
        insert_data(connection, "Service", service)
        for _ in range(random.randint(1, 3)):
            price = generate_price(service["id"])
            insert_data(connection, "Price", price)

    data_connections = []
    for team in teams:
        for _ in range(random.randint(1, 3)):
            data_connection = generate_data_connection_config(team["id"])
            insert_data(connection, "t_data_connection_config", data_connection)
            data_connections.append(data_connection)

    for team in teams:
        for _ in range(random.randint(0, 2)):
            source_conn = random.choice(data_connections)
            sink_conn = random.choice(data_connections)
            flink_cdc_config = generate_flink_cdc_config(
                team["id"], source_conn["id"], sink_conn["id"]
            )
            insert_data(connection, "t_flink_cdc_config", flink_cdc_config)

    connection.close()
    print("Data generation and insertion complete.")


if __name__ == "__main__":
    main()
