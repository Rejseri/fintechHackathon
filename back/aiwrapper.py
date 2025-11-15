"""
OpenAI integration for ESG report analysis.

This module provides functions to:
1. Extract raw parameter promises/commitments from ESG reports
2. Calculate derived metrics using paramcalculator.py
3. Validate raw parameters using web search
4. Return updated JSON templates with promises and truth values

Example usage:
    import json
    import aiwrapper
    
    # Load JSON template from data.json
    with open('data/data.json', 'r') as f:
        data = json.load(f)
        template = data['AKZA']  # Get template for a specific company
    
    # Get ESG report text (e.g., from PDF)
    esg_text = "..."  # Your ESG report text
    
    # Process the report
    result = aiwrapper.process_esg_report(esg_text, template)
    
    # result now contains:
    # - promise: extracted raw parameters + calculated derived metrics
    # - truth: true/false for each metric based on validation
    # Note: data.json is NOT modified, only the returned result is updated
"""

from openai import OpenAI
import config as key
import json
import copy
from typing import Dict, Any, List, Optional
from paramcalculator import EnvironmentalParameters, SocialParameters, GovernanceParameters

client = OpenAI(api_key=key.OPENAI_KEY)

# Define raw parameters that need to be extracted from ESG reports
# These map to the input parameters of paramcalculator classes
RAW_ENVIRONMENTAL_PARAMS = [
	"environmental_fines",
	"number_of_environmental_violations",  # maps to num_violations
	"number_of_spills_or_toxic_release_events",  # maps to num_spills
	"ghg_emissions_directly_associated",  # maps to ghg_emissions_direct
	"ghg_emission_scope_1",  # maps to ghg_emissions_scope1
	"energy_consumption",
	"water_usage",
	"active_environmental_lawsuits",  # maps to active_lawsuits
	"environmental_certifications",
	# Additional required for calculations
	"revenue",
	"operating_sites",
	"production_volume",
	"employees"
]

RAW_SOCIAL_PARAMS = [
	"fatalities",
	"worker_injury_rate",
	"number_of_strikes",  # maps to num_strikes
	"contractor_incident_rate",
	"glassdoor_average_rating",  # maps to glassdoor_rating
	"glassdoor_ceo_approval",
	"female_workforce_%",  # maps to female_workforce_pct
	"female_executive_%",  # maps to female_executive_pct
	"employee_turnover_%",  # maps to employee_turnover_pct
	# Additional required for calculations
	"employees"
]

RAW_GOVERNANCE_PARAMS = [
	"regulatory_investigations",
	"corruptions/bribery_cases",  # maps to corruption_cases
	"anti_competitive_behavior_fines",  # maps to anti_competitive_fines
	"board_independence_%",  # maps to board_independence_pct
	"number_of_financial_restatements",  # maps to financial_restatements
	"c-suit_turnover_rate",  # maps to csuite_turnover_rate
	"political_donations",
	"major_shareholder_lawsuits",
	# Note: num_lawsuits might need to be extracted separately or derived
	# Additional required for calculations
	"revenue",
	"operating_countries"
]

ALL_RAW_PARAMS = RAW_ENVIRONMENTAL_PARAMS + RAW_SOCIAL_PARAMS + RAW_GOVERNANCE_PARAMS
# Remove duplicates (like "employees" and "revenue")
ALL_RAW_PARAMS = list(dict.fromkeys(ALL_RAW_PARAMS))


def find_promises(esg_report_text: str, json_template: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Extract only raw parameter promises from ESG report text.
	Derived metrics will be calculated later using paramcalculator.
	
	Args:
		esg_report_text: The ESG report as text
		json_template: The JSON template from data.json (for a single company)
	
	Returns:
		A copy of the JSON template with only raw parameter promises populated
	"""
	# Create a deep copy to avoid modifying the original
	result = copy.deepcopy(json_template)
	
	# Limit text to avoid token limits
	limited_text = esg_report_text[:50000]
	
	# Create a prompt to extract only raw parameters
	prompt = f"""Analyze the following ESG report and extract specific promises, commitments, and claims for ONLY the following raw parameters.

ESG Report:
{limited_text}

Raw Parameters to Extract:
{json.dumps(ALL_RAW_PARAMS, indent=2)}

For each parameter, extract:
1. The specific promise/commitment/claim made in the report
2. Any numerical values mentioned
3. Any targets or goals stated

IMPORTANT: Only extract these raw parameters. Do NOT extract derived metrics like "fines_per_revenue" or "emissions_intensity" - those will be calculated later.

Return a JSON object where each key is one of the raw parameters above, and the value is either:
- A number if a specific value is mentioned
- A string describing the promise/commitment if no specific number is given
- null if no relevant promise is found for that parameter

Return ONLY valid JSON, no additional text."""

	try:
		response = client.chat.completions.create(
			model="gpt-4o",
			messages=[
				{"role": "system", "content": "You are an expert ESG analyst. Extract only raw parameters from ESG reports. Do not extract derived metrics. Return only valid JSON."},
				{"role": "user", "content": prompt}
			],
			response_format={"type": "json_object"},
			temperature=0.3
		)
		
		extracted_promises = json.loads(response.choices[0].message.content)
		
		# Update only raw parameters in the promise field
		for key in ALL_RAW_PARAMS:
			if key in extracted_promises and extracted_promises[key] is not None:
				result["promise"][key] = extracted_promises[key]
		
		return result
		
	except Exception as e:
		print(f"Error extracting promises: {e}")
		return result


def calculate_derived_metrics(raw_params: Dict[str, Any], json_template: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Calculate derived metrics using paramcalculator.py based on extracted raw parameters.
	
	Args:
		raw_params: Dictionary of raw parameter values extracted from ESG report
		json_template: The JSON template to update with calculated metrics
	
	Returns:
		Updated JSON template with derived metrics calculated and added to promise field
	"""
	result = copy.deepcopy(json_template)
	promise_dict = result.get("promise", {})
	
	# Helper function to get numeric value or default
	def get_numeric(key: str, default: float = 0.0) -> float:
		value = raw_params.get(key, promise_dict.get(key, default))
		if value is None:
			return default
		try:
			return float(value)
		except (ValueError, TypeError):
			return default
	
	# Get common values
	revenue = get_numeric("revenue", 1.0)  # Avoid division by zero
	employees = get_numeric("employees", 1.0)
	operating_sites = get_numeric("operating_sites", 1.0)
	production_volume = get_numeric("production_volume", 1.0)
	operating_countries = get_numeric("operating_countries", 1.0)
	
	# Calculate Environmental derived metrics
	try:
		env_params = EnvironmentalParameters(
			environmental_fines=get_numeric("environmental_fines"),
			num_violations=get_numeric("number_of_environmental_violations"),
			num_spills=get_numeric("number_of_spills_or_toxic_release_events"),
			ghg_emissions_direct=get_numeric("ghg_emissions_directly_associated"),
			ghg_emissions_scope1=get_numeric("ghg_emission_scope_1"),
			energy_consumption=get_numeric("energy_consumption"),
			water_usage=get_numeric("water_usage"),
			active_lawsuits=get_numeric("active_environmental_lawsuits"),
			environmental_certifications=get_numeric("environmental_certifications"),
			revenue=revenue,
			operating_sites=operating_sites,
			production_volume=production_volume,
			employees=employees
		)
		
		# Calculate and store derived environmental metrics
		if revenue > 0:
			promise_dict["environmental_fines_per_revenue"] = env_params.fines_per_revenue()
			promise_dict["violations_per_revenue"] = env_params.violations_per_revenue()
			promise_dict["emissions_intensity_(scope_1_per_revenue)"] = env_params.emissions_intensity()
			promise_dict["energy_intensity_(energy_per_revenue)"] = env_params.energy_intensity()
			promise_dict["water_intensity_(water_per_revenue)"] = env_params.water_intensity()
		
		if operating_sites > 0:
			promise_dict["environmental_fines_per_operating_site"] = env_params.fines_per_operating_site()
			promise_dict["violations_per_operating_site"] = env_params.violations_per_operating_site()
		
		if production_volume > 0:
			promise_dict["violations_per_production_volume"] = env_params.violations_per_production_volume()
			promise_dict["emissions_intensity_(scope_1_per_production_volume)"] = env_params.ghg_emissions_scope1 / production_volume
			promise_dict["energy_intensity_(energy_per_production_volume)"] = env_params.energy_consumption / production_volume
			promise_dict["water_intensity_(water_per_production_volume)"] = env_params.water_intensity() * revenue / production_volume
			promise_dict["spill_frequency_per_production_unit"] = env_params.spill_frequency_per_unit()
		
		if employees > 0:
			promise_dict["emissions_per_employee"] = env_params.emissions_per_employee()
			promise_dict["water_use_per_employee"] = env_params.water_per_employee()
		
		if env_params.energy_consumption > 0:
			promise_dict["energy_efficiency_ratio_(revenue_per_energy_consumed)"] = env_params.energy_efficiency_ratio()
		
		if env_params.ghg_emissions_scope1 > 0:
			promise_dict["carbon_efficiency_ratio_(revenue_per_ton_$co_{2}$)"] = env_params.carbon_efficiency_ratio()
		
		if operating_sites > 0:
			promise_dict["spill_frequency_per_site"] = env_params.num_spills / operating_sites
		
		if revenue > 0:
			promise_dict["active_environmental_lawsuits_per_revenue"] = env_params.active_lawsuits / revenue
		
		if operating_sites > 0:
			promise_dict["active_environmental_lawsuits_per_site"] = env_params.active_lawsuits / operating_sites
		
	except Exception as e:
		print(f"Error calculating environmental metrics: {e}")
	
	# Calculate Social derived metrics
	try:
		social_params = SocialParameters(
			fatalities=get_numeric("fatalities"),
			worker_injury_rate=get_numeric("worker_injury_rate"),
			num_strikes=get_numeric("number_of_strikes"),
			contractor_incident_rate=get_numeric("contractor_incident_rate"),
			glassdoor_rating=get_numeric("glassdoor_average_rating"),
			glassdoor_ceo_approval=get_numeric("glassdoor_ceo_approval"),
			female_workforce_pct=get_numeric("female_workforce_%"),
			female_executive_pct=get_numeric("female_executive_%"),
			employee_turnover_pct=get_numeric("employee_turnover_%"),
			employees=employees
		)
		
		# Calculate and store derived social metrics
		if employees > 0:
			promise_dict["fatalities_per_1,000_employees"] = social_params.fatalities_per_1000_employees()
			promise_dict["strikes_per_1,000_employees"] = social_params.strikes_per_1000_employees()
		
		promise_dict["total_recordable_incident_rate_(trir)"] = social_params.total_recordable_incident_rate()
		promise_dict["employee_engagement_proxy_(glassdoor_rating_ceo_approval)"] = social_params.employee_engagement_proxy()
		promise_dict["gender_representation_gap_(female_workforce_%_-_female_executive_%)"] = social_params.gender_representation_gap()
		promise_dict["retention_stability_index_(inverse_turnover)"] = social_params.retention_stability_index()
		
	except Exception as e:
		print(f"Error calculating social metrics: {e}")
	
	# Calculate Governance derived metrics
	try:
		# Note: num_lawsuits might need to be extracted or derived from other data
		num_lawsuits = get_numeric("major_shareholder_lawsuits", 0)  # Using as proxy if not available
		
		gov_params = GovernanceParameters(
			num_lawsuits=num_lawsuits,
			regulatory_investigations=get_numeric("regulatory_investigations"),
			corruption_cases=get_numeric("corruptions/bribery_cases"),
			anti_competitive_fines=get_numeric("anti_competitive_behavior_fines"),
			board_independence_pct=get_numeric("board_independence_%"),
			financial_restatements=get_numeric("number_of_financial_restatements"),
			csuite_turnover_rate=get_numeric("c-suit_turnover_rate"),
			political_donations=get_numeric("political_donations"),
			major_shareholder_lawsuits=get_numeric("major_shareholder_lawsuits"),
			revenue=revenue,
			operating_countries=operating_countries
		)
		
		# Calculate and store derived governance metrics
		if revenue > 0:
			promise_dict["lawsuits_per_revenue"] = gov_params.lawsuits_per_revenue()
			promise_dict["regulatory_investigations_per_revenue"] = gov_params.regulatory_investigations_per_revenue()
			promise_dict["corruption_cases_per_billion_revenue"] = gov_params.corruption_cases_per_billion_revenue()
			promise_dict["anti-competitive_fines_per_revenue"] = gov_params.anti_competitive_fines_per_revenue()
			promise_dict["political_donations_per_revenue"] = gov_params.political_donations_per_revenue()
			promise_dict["major_shareholder_lawsuits_per_billion_revenue"] = gov_params.major_shareholder_lawsuits_per_billion_revenue()
		
		if operating_countries > 0:
			promise_dict["lawsuits_per_operating_country"] = gov_params.lawsuits_per_operating_country()
			promise_dict["anti-competitive_violations_per_operating_country"] = gov_params.anti_competitive_violations_per_country()
		
		promise_dict["independent_directors_ratio"] = gov_params.independent_directors_ratio()
		promise_dict["executive_stability_index_(inverse_of_turnover)"] = gov_params.executive_stability_index()
		
	except Exception as e:
		print(f"Error calculating governance metrics: {e}")
	
	result["promise"] = promise_dict
	return result


def validate_claim_with_web_search(claim: str, company_name: str, metric_name: str) -> bool:
	"""
	Validate a specific ESG claim using OpenAI with web search capabilities.
	
	This function uses OpenAI's chat completions API. For better web search results,
	consider using OpenAI's Assistants API with web search enabled, or integrate
	with external web search APIs like Tavily, Serper, or Google Search API.
	
	Args:
		claim: The specific claim/promise to validate
		company_name: Name of the company
		metric_name: The metric name for context
	
	Returns:
		True if the claim is validated, False if contradicted or unverified
	"""
	if not claim or claim == "null" or str(claim).strip() == "":
		return False
	
	# Use OpenAI to search and validate the claim
	validation_prompt = f"""You are an ESG fact-checker. Validate the following claim made by {company_name}:

Claim: {claim}
Metric: {metric_name}

Based on your knowledge and available information, search for evidence that supports or contradicts this claim. Look for:
- News articles about the company
- Regulatory filings and SEC documents
- Third-party ESG reports
- Environmental violations, fines, or lawsuits
- Public records and government databases
- Industry reports and analysis

Consider:
- If the claim is contradicted by factual evidence (fines, violations, lawsuits), mark as FALSE
- If the claim is supported by credible evidence, mark as TRUE
- If you cannot find sufficient evidence to verify the claim, mark as FALSE (unverified claims are considered false)

Return your response as JSON with this structure:
{{
	"validated": true or false,
	"reasoning": "brief explanation of your finding"
}}

Return ONLY valid JSON."""

	try:
		# Using chat completions with GPT-4o
		# For production, consider using Assistants API with web search tool enabled
		response = client.chat.completions.create(
			model="gpt-4o",
			messages=[
				{"role": "system", "content": "You are an ESG fact-checker with access to current information. Validate ESG claims based on factual evidence. Be conservative - if evidence is unclear, mark as false."},
				{"role": "user", "content": validation_prompt}
			],
			response_format={"type": "json_object"},
			temperature=0.2
		)
		
		validation_result = json.loads(response.choices[0].message.content)
		return validation_result.get("validated", False)
		
	except Exception as e:
		print(f"Error validating claim '{claim}': {e}")
		return False


def find_truths(esg_report_text: str, json_template: Dict[str, Any], company_name: str = None) -> Dict[str, Any]:
	"""
	Validate only raw parameter claims using web search, then propagate truth to derived metrics.
	
	Args:
		esg_report_text: The ESG report as text
		json_template: The JSON template with promises already populated (raw + derived)
		company_name: Name of the company (optional, extracted from template if not provided)
	
	Returns:
		A copy of the JSON template with truth field updated (true/false for each metric)
	"""
	# Create a deep copy to avoid modifying the original
	result = copy.deepcopy(json_template)
	
	# Get company name from template if not provided
	if not company_name:
		company_name = json_template.get("name", "Unknown Company")
	
	# Get promises and truth keys
	promise_dict = json_template.get("promise", {})
	truth_dict = result.get("truth", {})
	
	# Step 1: Validate only raw parameters
	raw_truth = {}
	for param_name in ALL_RAW_PARAMS:
		if param_name in promise_dict:
			promise_value = promise_dict[param_name]
			if promise_value is None or promise_value == "":
				# No promise found, mark as false
				raw_truth[param_name] = False
			else:
				# Convert promise to string for validation
				claim = str(promise_value)
				# Validate the claim
				is_valid = validate_claim_with_web_search(claim, company_name, param_name)
				raw_truth[param_name] = is_valid
		else:
			raw_truth[param_name] = False
	
	# Step 2: Propagate truth to derived metrics
	# For derived metrics, if all underlying raw parameters are true, the derived metric is true
	# (assuming the calculation itself is correct)
	
	# Map derived metrics to their raw parameter dependencies
	derived_dependencies = {
		# Environmental derived metrics
		"environmental_fines_per_revenue": ["environmental_fines", "revenue"],
		"environmental_fines_per_operating_site": ["environmental_fines", "operating_sites"],
		"violations_per_revenue": ["number_of_environmental_violations", "revenue"],
		"violations_per_operating_site": ["number_of_environmental_violations", "operating_sites"],
		"violations_per_production_volume": ["number_of_environmental_violations", "production_volume"],
		"emissions_intensity_(scope_1_per_revenue)": ["ghg_emission_scope_1", "revenue"],
		"emissions_intensity_(scope_1_per_production_volume)": ["ghg_emission_scope_1", "production_volume"],
		"emissions_per_employee": ["ghg_emission_scope_1", "employees"],
		"energy_intensity_(energy_per_revenue)": ["energy_consumption", "revenue"],
		"energy_intensity_(energy_per_production_volume)": ["energy_consumption", "production_volume"],
		"energy_efficiency_ratio_(revenue_per_energy_consumed)": ["energy_consumption", "revenue"],
		"carbon_efficiency_ratio_(revenue_per_ton_$co_{2}$)": ["ghg_emission_scope_1", "revenue"],
		"water_intensity_(water_per_revenue)": ["water_usage", "revenue"],
		"water_intensity_(water_per_production_volume)": ["water_usage", "production_volume"],
		"water_use_per_employee": ["water_usage", "employees"],
		"spill_frequency_per_site": ["number_of_spills_or_toxic_release_events", "operating_sites"],
		"spill_frequency_per_production_unit": ["number_of_spills_or_toxic_release_events", "production_volume"],
		"active_environmental_lawsuits_per_revenue": ["active_environmental_lawsuits", "revenue"],
		"active_environmental_lawsuits_per_site": ["active_environmental_lawsuits", "operating_sites"],
		
		# Social derived metrics
		"fatalities_per_1,000_employees": ["fatalities", "employees"],
		"strikes_per_1,000_employees": ["number_of_strikes", "employees"],
		"total_recordable_incident_rate_(trir)": ["contractor_incident_rate"],
		"employee_engagement_proxy_(glassdoor_rating_ceo_approval)": ["glassdoor_average_rating", "glassdoor_ceo_approval"],
		"gender_representation_gap_(female_workforce_%_-_female_executive_%)": ["female_workforce_%", "female_executive_%"],
		"retention_stability_index_(inverse_turnover)": ["employee_turnover_%"],
		
		# Governance derived metrics
		"lawsuits_per_revenue": ["major_shareholder_lawsuits", "revenue"],  # Using proxy
		"regulatory_investigations_per_revenue": ["regulatory_investigations", "revenue"],
		"corruption_cases_per_billion_revenue": ["corruptions/bribery_cases", "revenue"],
		"anti-competitive_fines_per_revenue": ["anti_competitive_behavior_fines", "revenue"],
		"political_donations_per_revenue": ["political_donations", "revenue"],
		"major_shareholder_lawsuits_per_billion_revenue": ["major_shareholder_lawsuits", "revenue"],
		"lawsuits_per_operating_country": ["major_shareholder_lawsuits", "operating_countries"],
		"anti-competitive_violations_per_operating_country": ["anti_competitive_behavior_fines", "operating_countries"],
		"independent_directors_ratio": ["board_independence_%"],
		"executive_stability_index_(inverse_of_turnover)": ["c-suit_turnover_rate"],
	}
	
	# Set truth for all metrics
	for metric_name in promise_dict.keys():
		if metric_name in ALL_RAW_PARAMS:
			# Raw parameter - use validated truth
			truth_dict[metric_name] = raw_truth.get(metric_name, False)
		elif metric_name in derived_dependencies:
			# Derived metric - true if all dependencies are true
			deps = derived_dependencies[metric_name]
			truth_dict[metric_name] = all(raw_truth.get(dep, False) for dep in deps)
		else:
			# Unknown metric - default to false
			truth_dict[metric_name] = False
	
	result["truth"] = truth_dict
	return result


def process_esg_report(esg_report_text: str, json_template: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Main function to process an ESG report:
	1. Extract raw parameter promises from ESG report
	2. Calculate derived metrics using paramcalculator.py
	3. Validate raw parameters using web search
	4. Propagate truth to derived metrics
	
	Args:
		esg_report_text: The ESG report as text
		json_template: The JSON template from data.json (for a single company)
	
	Returns:
		Updated JSON template with:
		- promise: raw parameters (extracted) + derived metrics (calculated)
		- truth: true/false for all metrics (raw validated, derived propagated)
	"""
	# Step 1: Extract only raw parameter promises from ESG report
	print("Extracting raw parameter promises from ESG report...")
	result = find_promises(esg_report_text, json_template)
	
	# Step 2: Calculate derived metrics using paramcalculator
	print("Calculating derived metrics using paramcalculator...")
	raw_params = {k: v for k, v in result.get("promise", {}).items() if k in ALL_RAW_PARAMS}
	result = calculate_derived_metrics(raw_params, result)
	
	# Step 3: Validate raw parameters and propagate truth to derived metrics
	print("Validating raw parameters with web search...")
	result = find_truths(esg_report_text, result)
	
	return result
