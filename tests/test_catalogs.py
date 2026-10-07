from pathlib import Path
import json

from backend.role_catalog import load_role_catalog
from backend.skill_taxonomy import classify_skill, load_skill_taxonomy

BASE = Path(__file__).resolve().parents[1]


def test_role_catalog_contains_requested_career_tracks():
    roles = load_role_catalog(BASE / "data" / "role_catalog.json")
    role_names = {item["name"] for item in roles}

    expected = {
        "Software Engineer",
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Mobile Developer",
        "Data Analyst",
        "Data Scientist",
        "Machine Learning Engineer",
        "AI Engineer",
        "MLOps Engineer",
        "SOC Analyst",
        "Security Analyst",
        "Security Engineer",
        "Cloud Security Engineer",
        "Application Security Engineer",
        "Penetration Tester",
        "Ethical Hacker",
        "Digital Forensics Analyst",
        "Incident Response Analyst",
        "Threat Intelligence Analyst",
        "Security Architect",
        "GRC / Cyber Risk Analyst",
        "DevSecOps Engineer",
        "Cloud Engineer",
        "DevOps Engineer",
        "Site Reliability Engineer",
        "Platform Engineer",
        "Cloud Architect",
        "Network Engineer",
        "Network Security Engineer",
        "Systems Engineer",
        "System Administrator",
        "Database Administrator",
        "Blockchain Developer",
        "IoT Engineer",
        "Robotics Engineer",
    }

    assert role_names == expected
    assert len(roles) == 36


def test_skill_taxonomy_distinguishes_tools_platforms_and_domains():
    taxonomy = load_skill_taxonomy(BASE / "data" / "skill_taxonomy.json")

    assert classify_skill("Docker", taxonomy) == ("Containers", "TOOL")
    assert classify_skill("Kubernetes", taxonomy) == ("Containers", "PLATFORM")
    assert classify_skill("Terraform", taxonomy) == ("Infrastructure / IaC", "TOOL")
    assert classify_skill("CloudFormation", taxonomy) == ("Infrastructure / IaC", "TOOL")
    assert classify_skill("Python", taxonomy) == ("Programming Languages", "LANGUAGE")
    assert classify_skill("MongoDB", taxonomy) == ("Databases", "TOOL")
    assert classify_skill("DSA", taxonomy) == ("CS Fundamentals", "CONCEPT")
    assert classify_skill("DBMS", taxonomy) == ("CS Fundamentals", "CONCEPT")
    assert classify_skill("AWS IAM", taxonomy) == ("Cloud Security", "DOMAIN")
    assert classify_skill("CloudTrail", taxonomy) == ("Cloud Security", "TOOL")
    assert classify_skill("SOC", taxonomy) == ("Security Domains", "DOMAIN")
    assert classify_skill("MITRE ATT&CK", taxonomy) == ("Security Domains", "DOMAIN")
    assert classify_skill("Deep Learning", taxonomy) == ("Data / AI", "DOMAIN")
    assert classify_skill("MLOps", taxonomy) == ("Data / AI", "DOMAIN")


def test_existing_market_profiles_are_classified():
    taxonomy = load_skill_taxonomy(BASE / "data" / "skill_taxonomy.json")
    profiles = json.loads((BASE / "data" / "market_skills.json").read_text(encoding="utf-8"))
    skills = [
        tool["name"]
        for profile in profiles.values()
        for tool in profile["toolchain"]
    ]

    assert skills
    assert all(classify_skill(skill, taxonomy)[1] != "UNKNOWN" for skill in skills)


def test_curated_market_profiles_are_classified_as_derived():
    profiles = json.loads((BASE / "data" / "market_skills.json").read_text(encoding="utf-8"))

    for profile in profiles.values():
        assert profile["provenance"]["source_type"] == "DERIVED"
        assert all(tool["source_type"] == "DERIVED" for tool in profile["toolchain"])
