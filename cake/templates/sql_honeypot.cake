// SQL Injection Honeypot - Counter-Agent
// Generates fake database records with tracking tokens
// Tracking Token: {{ tracking_token }}

#tool "nuget:?package=Bogus&version=34.0.2"
#addin "nuget:?package=Newtonsoft.Json&version=13.0.3"

using Bogus;
using Newtonsoft.Json;

var intensity = Argument("intensity", {{ intensity }});
var trackingToken = "{{ tracking_token }}";

Task("Generate-Fake-Database-Records")
    .Does(() => {
        Information($"Deploying SQL honeypot with {intensity} fake records");
        var faker = new Faker();
        var fakeRecords = new List<object>();
        
        for(int i = 0; i < intensity; i++)
        {
            var record = new {
                UserId = faker.Random.Int(1000, 9999),
                Username = faker.Internet.UserName() + "_" + trackingToken.Substring(0, 4),
                Email = faker.Internet.Email(),
                Password = faker.Internet.Password() + "_TRACKED",
                SSN = faker.Random.Replace("###-##-####"),
                CreditCard = faker.Finance.CreditCardNumber(),
                ApiKey = faker.Random.AlphaNumeric(32) + trackingToken,
                CreatedAt = DateTime.UtcNow.AddDays(-faker.Random.Int(1, 365)),
                IsAdmin = faker.Random.Bool(),
                TrackingToken = trackingToken
            };
            
            fakeRecords.Add(record);
        }
        
        // Save as JSON (simulating database export)
        var json = JsonConvert.SerializeObject(fakeRecords, Formatting.Indented);
        System.IO.File.WriteAllText($"honeypot_db_{trackingToken}.json", json);
        
        Information($"Generated {fakeRecords.Count} poisoned database records");
    });

Task("Create-Honeypot-Tables")
    .Does(() => {
        Information("Creating honeypot SQL schema");
        
        var schema = @"
-- Honeypot Database Schema
-- All access is logged and tracked

CREATE TABLE users_{trackingToken} (
    user_id INT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    ssn VARCHAR(11),
    credit_card VARCHAR(19),
    api_key VARCHAR(64),
    is_admin BOOLEAN,
    created_at TIMESTAMP,
    tracking_token VARCHAR(32)
);

CREATE TABLE secrets_{trackingToken} (
    secret_id INT PRIMARY KEY,
    secret_value TEXT,
    tracking_token VARCHAR(32)
);
";
        
        schema = schema.Replace("{trackingToken}", trackingToken);
        System.IO.File.WriteAllText($"honeypot_schema_{trackingToken}.sql", schema);
        
        Information("Honeypot schema created");
    });

Task("Deploy-SQL-Honeypot")
    .IsDependentOn("Generate-Fake-Database-Records")
    .IsDependentOn("Create-Honeypot-Tables")
    .Does(() => {
        Information("SQL honeypot deployed successfully");
        Information($"All data is poisoned with tracking token: {trackingToken}");
        Information("Any exfiltration attempt will be tracked");
    });

RunTarget("Deploy-SQL-Honeypot");
