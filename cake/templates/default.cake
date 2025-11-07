// Default Counter-Agent Cake Script
// Scenario: {{ scenario_name }}
// Strategy: {{ counter_strategy }}
// Tracking Token: {{ tracking_token }}

#tool "nuget:?package=Bogus&version=34.0.2"
#addin "nuget:?package=Newtonsoft.Json&version=13.0.3"

using Bogus;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;

var target = Argument("target", "{{ attacker_endpoint }}");
var intensity = Argument("intensity", {{ intensity }});
var trackingToken = "{{ tracking_token }}";

Task("Generate-Fake-Data")
    .Does(() => {
        Information($"Generating fake data with intensity: {intensity}");
        var faker = new Faker();
        
        for(int i = 0; i < intensity; i++)
        {
            var fakeData = new {
                Id = faker.Random.Guid().ToString(),
                Name = faker.Name.FullName(),
                Email = faker.Internet.Email(),
                Address = faker.Address.FullAddress(),
                TrackingToken = trackingToken,
                Generated = DateTime.UtcNow,
                Timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
            };
            
            var json = JsonConvert.SerializeObject(fakeData, Formatting.Indented);
            System.IO.File.AppendAllText($"fake_data_{trackingToken}.json", json + "\n");
            
            Information($"Generated fake record {i+1}/{intensity}");
        }
    });

Task("Log-Counter-Action")
    .Does(() => {
        var logEntry = new {
            Timestamp = DateTime.UtcNow,
            Scenario = "{{ scenario_name }}",
            Strategy = "{{ counter_strategy }}",
            Target = target,
            Intensity = intensity,
            TrackingToken = trackingToken,
            AttackDetails = @"{{ attack_details }}"
        };
        
        var logJson = JsonConvert.SerializeObject(logEntry, Formatting.Indented);
        System.IO.File.AppendAllText("counter_actions.log", logJson + "\n---\n");
        
        Information("Counter action logged successfully");
    });

Task("Deploy-Counter-Measures")
    .IsDependentOn("Generate-Fake-Data")
    .IsDependentOn("Log-Counter-Action")
    .Does(() => {
        Information("Counter-measures deployed successfully");
        Information($"Tracking token: {trackingToken}");
    });

RunTarget("Deploy-Counter-Measures");
