// Flood Agent - Counter API Scraping
// Deploys multiple agents to flood attacker with false data
// Tracking Token: {{ tracking_token }}

#tool "nuget:?package=Bogus&version=34.0.2"
#addin "nuget:?package=Newtonsoft.Json&version=13.0.3"

using Bogus;
using Newtonsoft.Json;
using System;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Net.Http;

var intensity = Argument("intensity", {{ intensity }});
var trackingToken = "{{ tracking_token }}";
var attackerIp = "{{ attacker_ip }}";

Task("Generate-Agent-Swarm")
    .Does(() => {
        Information($"Deploying {intensity} counter-agents to flood attacker");
        
        var agents = new List<object>();
        var faker = new Faker();
        
        // Create multiple fake agent identities
        for(int i = 0; i < intensity; i++)
        {
            var agent = new {
                AgentId = $"agent_{i}_{trackingToken.Substring(0, 6)}",
                Name = faker.Name.FullName(),
                Email = faker.Internet.Email(),
                ApiKey = faker.Random.AlphaNumeric(32) + "_" + trackingToken,
                Endpoint = faker.Internet.Url(),
                UserAgent = faker.Internet.UserAgent(),
                CreatedAt = DateTime.UtcNow
            };
            
            agents.Add(agent);
        }
        
        var json = JsonConvert.SerializeObject(agents, Formatting.Indented);
        System.IO.File.WriteAllText($"flood_agents_{trackingToken}.json", json);
        
        Information($"Created {agents.Count} counter-agents");
    });

Task("Generate-Fake-API-Responses")
    .Does(() => {
        Information("Generating fake API response data");
        var faker = new Faker();
        var responses = new List<object>();
        
        // Generate many fake responses to waste attacker's resources
        for(int i = 0; i < intensity * 10; i++)
        {
            var response = new {
                Id = faker.Random.Guid(),
                Data = new {
                    Users = Enumerable.Range(0, 5).Select(_ => new {
                        UserId = faker.Random.Int(1000, 9999),
                        Username = faker.Internet.UserName() + "_tracked",
                        Email = faker.Internet.Email(),
                        TrackingToken = trackingToken
                    }).ToList(),
                    Products = Enumerable.Range(0, 3).Select(_ => new {
                        ProductId = faker.Random.Guid(),
                        Name = faker.Commerce.ProductName(),
                        Price = faker.Commerce.Price(),
                        TrackingToken = trackingToken
                    }).ToList()
                },
                Timestamp = DateTime.UtcNow,
                RequestId = faker.Random.AlphaNumeric(16),
                TrackingToken = trackingToken
            };
            
            responses.Add(response);
        }
        
        // Split into multiple files to increase complexity
        var chunkSize = intensity > 50 ? 50 : intensity;
        for(int i = 0; i < responses.Count; i += chunkSize)
        {
            var chunk = responses.Skip(i).Take(chunkSize).ToList();
            var json = JsonConvert.SerializeObject(chunk, Formatting.Indented);
            System.IO.File.WriteAllText($"fake_responses_{trackingToken}_{i / chunkSize}.json", json);
        }
        
        Information($"Generated {responses.Count} fake API responses in multiple files");
    });

Task("Create-Contradictory-Data")
    .Does(() => {
        Information("Creating contradictory data to confuse ML models");
        var faker = new Faker();
        
        // Generate data with intentional contradictions
        var contradictions = new {
            UserData = new[] {
                new { UserId = 1, Name = "Alice", Email = "alice@example.com" },
                new { UserId = 1, Name = "Bob", Email = "bob@example.com" },  // Same ID, different data
                new { UserId = 1, Name = "Charlie", Email = "charlie@example.com" }
            },
            ProductData = new[] {
                new { ProductId = "A123", Price = 10.00, InStock = true },
                new { ProductId = "A123", Price = 99.99, InStock = false },  // Same ID, contradictory
                new { ProductId = "A123", Price = 5.50, InStock = true }
            },
            TrackingToken = trackingToken,
            Note = "This data contains intentional contradictions to poison ML model training"
        };
        
        var json = JsonConvert.SerializeObject(contradictions, Formatting.Indented);
        System.IO.File.WriteAllText($"contradictory_data_{trackingToken}.json", json);
        
        Information("Contradictory data generated - will confuse scrapers training ML models");
    });

Task("Simulate-Rate-Limiting")
    .Does(() => {
        Information("Simulating progressive rate limiting");
        
        var rateLimitConfig = new {
            Message = "Rate limit applied to suspicious client",
            AttackerIP = attackerIp,
            TrackingToken = trackingToken,
            Limits = new[] {
                new { Stage = 1, RequestsPerMinute = 100, Message = "Warning: High request rate" },
                new { Stage = 2, RequestsPerMinute = 50, Message = "Rate limited" },
                new { Stage = 3, RequestsPerMinute = 10, Message = "Severe rate limit" },
                new { Stage = 4, RequestsPerMinute = 1, Message = "Heavily throttled" }
            },
            Timestamp = DateTime.UtcNow
        };
        
        var json = JsonConvert.SerializeObject(rateLimitConfig, Formatting.Indented);
        System.IO.File.WriteAllText($"rate_limit_config_{trackingToken}.json", json);
        
        Information("Rate limiting configuration created");
    });

Task("Deploy-Flood-Countermeasures")
    .IsDependentOn("Generate-Agent-Swarm")
    .IsDependentOn("Generate-Fake-API-Responses")
    .IsDependentOn("Create-Contradictory-Data")
    .IsDependentOn("Simulate-Rate-Limiting")
    .Does(() => {
        Information("====================================");
        Information("Flood countermeasures deployed!");
        Information($"Tracking Token: {trackingToken}");
        Information($"Counter-agents: {intensity}");
        Information($"Fake responses: {intensity * 10}");
        Information("Attacker will receive:");
        Information("  - False data with tracking tokens");
        Information("  - Contradictory data to poison ML training");
        Information("  - Progressive rate limiting");
        Information("  - Resource exhaustion tactics");
        Information("====================================");
    });

RunTarget("Deploy-Flood-Countermeasures");
