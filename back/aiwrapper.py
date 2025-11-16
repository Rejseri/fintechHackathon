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
import time
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

# Basic operational parameters that don't need validation
# These are factual metrics that companies wouldn't lie about
BASIC_PARAMS_EXCLUDED_FROM_VALIDATION = [
	"revenue",
	"operating_sites",  # number of factories
	"employees",  # employee number
	"production_volume",
	"operating_countries"
]


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
	print(f"  ESG report text length: {len(esg_report_text)} chars (using first {len(limited_text)} chars)")
	print(f"  Extracting {len(ALL_RAW_PARAMS)} raw parameters from ESG report...")
	
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
		print("  Calling OpenAI API to extract promises...")
		response = client.chat.completions.create(
			model="gpt-5-nano",
			messages=[
				{"role": "system", "content": "You are an expert ESG analyst. Extract only raw parameters from ESG reports. Do not extract derived metrics. Return only valid JSON."},
				{"role": "user", "content": prompt}
			],
			response_format={"type": "json_object"},
		)
		print("  OpenAI API response received")
		
		extracted_promises = json.loads(response.choices[0].message.content)
		print(f"  Extracted {len(extracted_promises)} parameter values from API response")
		
		# Update only raw parameters in the promise field
		promises_found = 0
		for key in ALL_RAW_PARAMS:
			if key in extracted_promises and extracted_promises[key] is not None:
				result["promise"][key] = extracted_promises[key]
				promises_found += 1
		
		print(f"  Successfully extracted {promises_found} raw parameter promises")
		return result
		
	except Exception as e:
		print(f"  ERROR extracting promises: {e}")
		import traceback
		traceback.print_exc()
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
	
	print(f"  Common values: revenue={revenue}, employees={employees}, operating_sites={operating_sites}, production_volume={production_volume}, operating_countries={operating_countries}")
	
	# Calculate Environmental derived metrics
	print("  Calculating Environmental derived metrics...")
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
		
		env_metrics_count = sum(1 for k in promise_dict.keys() if k.startswith(("environmental_", "violations_", "emissions_", "energy_", "water_", "spill_", "active_environmental_")))
		print(f"  Calculated {env_metrics_count} Environmental derived metrics")
		
	except Exception as e:
		print(f"  ERROR calculating environmental metrics: {e}")
		import traceback
		traceback.print_exc()
	
	# Calculate Social derived metrics
	print("  Calculating Social derived metrics...")
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
		
		social_metrics_count = sum(1 for k in promise_dict.keys() if any(k.startswith(prefix) for prefix in ["fatalities_", "strikes_", "total_recordable_", "employee_engagement_", "gender_representation_", "retention_stability_"]))
		print(f"  Calculated {social_metrics_count} Social derived metrics")
		
	except Exception as e:
		print(f"  ERROR calculating social metrics: {e}")
		import traceback
		traceback.print_exc()
	
	# Calculate Governance derived metrics
	print("  Calculating Governance derived metrics...")
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
		
		gov_metrics_count = sum(1 for k in promise_dict.keys() if any(k.startswith(prefix) for prefix in ["lawsuits_", "regulatory_", "corruption_", "anti-competitive_", "political_", "independent_directors_", "executive_stability_"]))
		print(f"  Calculated {gov_metrics_count} Governance derived metrics")
		
	except Exception as e:
		print(f"  ERROR calculating governance metrics: {e}")
		import traceback
		traceback.print_exc()
	
	result["promise"] = promise_dict
	total_derived = len([k for k in promise_dict.keys() if k not in ALL_RAW_PARAMS])
	print(f"  Total derived metrics calculated: {total_derived}")
	return result


def validate_claim_with_web_search(claim: str, company_name: str, metric_name: str) -> tuple[bool, List[Dict[str, str]]]:
	"""
	Check if an ESG claim can be invalidated using OpenAI with web search capabilities.
	
	This function searches for evidence that CONTRADICTS or INVALIDATES the claim.
	- If contradictory evidence is found, the claim is marked as invalid (False) and sources are returned
	- If no contradictory evidence is found, the claim is considered valid (True) and no sources are returned
	
	This function uses OpenAI's responses API with web search tool enabled.
	
	Args:
		claim: The specific claim/promise to check
		company_name: Name of the company
		metric_name: The metric name for context
	
	Returns:
		Tuple of (is_valid: bool, sources: List[Dict[str, str]])
		- is_valid: True if no invalidation evidence found (claim stands), False if invalidated
		- sources: List of source dictionaries with 'url' and 'description' keys (only returned if claim is invalidated)
	"""
	if not claim or claim == "null" or str(claim).strip() == "":
		return False, []
	
	print(f"    Checking for invalidation evidence for '{metric_name}': {claim[:100]}...")
	
	# Use OpenAI to search for evidence that invalidates the claim
	# Optimized prompt to reduce token usage
	validation_prompt = f"""Find evidence that INVALIDATES this claim by {company_name}:

Claim: {claim}
Metric: {metric_name}

Search for: violations, fines, lawsuits, regulatory actions, or negative news that contradicts this claim.

Rules:
- If contradictory evidence found → mark "invalidated": true and include sources
- If no contradiction found → mark "invalidated": false (claim stands) and leave sources as empty array

Return JSON only:
{{
	"invalidated": true or false,
	"reasoning": "brief explanation of why the claim is invalidated or valid",
	"sources": [
		{{
			"url": "https://example.com/article",
			"description": "Brief description of how this source contradicts the claim"
		}}
	]
}}

IMPORTANT:
- Include sources ONLY if invalidated is true
- Each source must have a valid URL and description
- If invalidated is false, return empty sources array: "sources": []
- Use actual URLs from web search results, not placeholder URLs"""

	try:
		# Using responses API with web search tool enabled
		# Optimized prompt - removed redundant instructions
		full_prompt = f"""ESG fact-checker. Find evidence that INVALIDATES claims. If no contradiction found, claim is valid.

{validation_prompt}"""
		
		response = client.responses.create(
			model="gpt-5-nano",
			tools=[{"type": "web_search"}],
			input=full_prompt
		)
		
		# Extract text from response
		# Response is iterable and contains a list of objects with different types
		output_text = ""
		
		# Check if response has output_text attribute (direct access)
		if hasattr(response, 'output_text'):
			output_text = response.output_text or ""
		
		# Iterate through response items (response is iterable)
		for item in response:
			if isinstance(item, dict):
				# Check for message type items
				if item.get('type') == 'message' and item.get('role') == 'assistant':
					content = item.get('content', [])
					if isinstance(content, list):
						for content_item in content:
							if isinstance(content_item, dict):
								# Extract text from output_text type items
								if content_item.get('type') == 'output_text':
									text = content_item.get('text', '')
									if text:
										output_text += text
		
		# Parse validation result from output text (sources are now in the JSON)
		validation_result = {}
		sources = []
		
		if output_text:
			try:
				validation_result = json.loads(output_text)
			except json.JSONDecodeError:
				# If not valid JSON, try to extract JSON from the text
				# Look for JSON object in the text - need to handle nested objects for sources array
				import re
				# Try to find JSON with "invalidated" key - use a more robust pattern
				# Match from first { to last } that contains "invalidated" and "sources"
				# This pattern tries to match balanced braces to get the full JSON object
				json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', output_text, re.DOTALL)
				if json_match:
					try:
						validation_result = json.loads(json_match.group())
					except:
						# Try to find and fix common JSON issues
						json_str = json_match.group()
						# Remove trailing commas before closing braces/brackets
						json_str = re.sub(r',\s*}', '}', json_str)
						json_str = re.sub(r',\s*]', ']', json_str)
						try:
							validation_result = json.loads(json_str)
						except:
							# Last resort: try to extract just the fields we need
							print(f"      WARNING: Could not parse full JSON, attempting partial extraction")
							invalidated_match = re.search(r'"invalidated"\s*:\s*(true|false)', output_text, re.IGNORECASE)
							if invalidated_match:
								validation_result["invalidated"] = invalidated_match.group(1).lower() == "true"
							reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]*)"', output_text)
							if reasoning_match:
								validation_result["reasoning"] = reasoning_match.group(1)
							validation_result["sources"] = []  # Will try to extract sources separately
		
		# Extract sources from the JSON validation result
		if isinstance(validation_result, dict):
			sources_data = validation_result.get("sources", [])
			if isinstance(sources_data, list):
				for source in sources_data:
					if isinstance(source, dict):
						url = source.get("url", "").strip()
						description = source.get("description", "").strip()
						if url and url.startswith(("http://", "https://")):
							sources.append({
								"url": url,
								"description": description or f"Evidence contradicting {metric_name} claim"
							})
		
		# Check if claim was invalidated
		# If invalidated is True, the claim is FALSE (not valid)
		# If invalidated is False or not found, the claim is TRUE (valid - no contradiction found)
		is_invalidated = validation_result.get("invalidated", False)
		is_valid = not is_invalidated  # Valid if NOT invalidated
		
		reasoning = validation_result.get("reasoning", "No reasoning provided")
		
		# Only show sources if the claim was invalidated (sources are the evidence of invalidation)
		display_sources = sources if is_invalidated else []
		
		print(f"      Result: {'✗ INVALIDATED' if is_invalidated else '✓ VALID (no contradiction found)'} - {reasoning[:80]}")
		if display_sources:
			print(f"      Found {len(display_sources)} source(s) contradicting the claim")
			for idx, src in enumerate(display_sources, 1):
				print(f"        Source {idx}: {src.get('url', 'NO URL')[:60]}... - {src.get('description', 'NO DESCRIPTION')[:50]}")
		
		return is_valid, display_sources
		
	except Exception as e:
		print(f"      ERROR validating claim: {e}")
		import traceback
		traceback.print_exc()
		return False, []


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
	
	print(f"  Validating claims for company: {company_name}")
	
	# Get promises and truth keys
	promise_dict = json_template.get("promise", {})
	truth_dict = result.get("truth", {})
	
	# Step 1: Validate only raw parameters that were actually found in the ESG report
	# Only validate parameters that have non-null, non-empty values (i.e., were extracted from the report)
	# Exclude basic operational parameters that don't need validation
	params_to_validate = []
	for param_name in ALL_RAW_PARAMS:
		# Skip basic parameters that don't need validation
		if param_name in BASIC_PARAMS_EXCLUDED_FROM_VALIDATION:
			continue
		if param_name in promise_dict:
			promise_value = promise_dict[param_name]
			# Only include parameters that were actually found in the report
			if promise_value is not None and promise_value != "":
				params_to_validate.append(param_name)
	
	print(f"  Step 1: Validating {len(params_to_validate)} parameters found in ESG report (out of {len(ALL_RAW_PARAMS)} total)...")
	raw_truth = {}
	all_sources = []  # Collect all sources from validations
	metric_sources = {}  # Map metric names to their sources
	
	# Initialize all raw parameters
	# Basic parameters are set to True (not validated, assumed truthful)
	# Other parameters default to False (will be validated)
	for param_name in ALL_RAW_PARAMS:
		if param_name in BASIC_PARAMS_EXCLUDED_FROM_VALIDATION:
			raw_truth[param_name] = True  # Assume basic parameters are truthful
		else:
			raw_truth[param_name] = False  # Will be validated
		metric_sources[param_name] = []
	
	# Only validate parameters that were actually extracted from the report
	for i, param_name in enumerate(params_to_validate, 1):
		promise_value = promise_dict[param_name]
		# Convert promise to string for validation
		claim = str(promise_value)
		# Validate the claim and get sources
		print(f"    [{i}/{len(params_to_validate)}] Validating: {param_name}")
		
		# Add rate limiting to avoid hitting API limits
		# Small delay between requests to respect rate limits
		if i > 1:  # Don't delay before first request
			time.sleep(1.5)  # 1.5 second delay between requests
		
		try:
			is_valid, sources = validate_claim_with_web_search(claim, company_name, param_name)
			raw_truth[param_name] = is_valid
			# Store sources for this specific metric
			metric_sources[param_name] = sources
			# Add sources to collection
			all_sources.extend(sources)
		except Exception as e:
			# Handle rate limit errors with exponential backoff
			error_str = str(e).lower()
			if "rate_limit" in error_str or "429" in error_str or "quota" in error_str:
				print(f"      Rate limit hit for {param_name}, waiting 10 seconds before retry...")
				time.sleep(10)
				try:
					is_valid, sources = validate_claim_with_web_search(claim, company_name, param_name)
					raw_truth[param_name] = is_valid
					metric_sources[param_name] = sources
					all_sources.extend(sources)
				except Exception as retry_error:
					print(f"      Retry failed for {param_name}: {retry_error}")
					# Default to valid on persistent errors
					raw_truth[param_name] = True
					metric_sources[param_name] = []
			else:
				print(f"      Error validating {param_name}: {e}")
				# Default to valid on other errors
				raw_truth[param_name] = True
				metric_sources[param_name] = []
	
	validated_count = sum(1 for v in raw_truth.values() if v)
	print(f"  Validation complete: {validated_count}/{len(params_to_validate)} validated parameters marked as TRUE")
	print(f"  Collected {len(all_sources)} total sources from validations")
	
	# Step 2: Propagate truth to derived metrics
	# For derived metrics, if all underlying raw parameters are true, the derived metric is true
	# (assuming the calculation itself is correct)
	
	print(f"  Step 2: Propagating truth to derived metrics...")
	
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
	derived_count = 0
	derived_true_count = 0
	for metric_name in promise_dict.keys():
		if metric_name in ALL_RAW_PARAMS:
			# Raw parameter - use validated truth
			truth_dict[metric_name] = raw_truth.get(metric_name, False)
		elif metric_name in derived_dependencies:
			# Derived metric - true if all dependencies are true
			deps = derived_dependencies[metric_name]
			is_true = all(raw_truth.get(dep, False) for dep in deps)
			truth_dict[metric_name] = is_true
			derived_count += 1
			if is_true:
				derived_true_count += 1
		else:
			# Unknown metric - default to false
			truth_dict[metric_name] = False
	
	print(f"  Propagated truth to {derived_count} derived metrics ({derived_true_count} validated as TRUE)")
	
	result["truth"] = truth_dict
	
	# Store sources in result (remove duplicates based on URL)
	unique_sources = []
	seen_urls = set()
	for source in all_sources:
		url = source.get("url", "")
		if url and url not in seen_urls:
			seen_urls.add(url)
			unique_sources.append(source)
	
	result["sources"] = unique_sources
	
	# Store sources per metric for frontend access
	result["metric_sources"] = metric_sources
	print(f"  Stored {len(unique_sources)} unique sources")
	print(f"  Stored sources for {len([k for k, v in metric_sources.items() if v])} metrics")
	
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
	company_name = json_template.get("name", "Unknown Company")
	print(f"\n{'='*60}")
	print(f"Processing ESG report for: {company_name}")
	print(f"{'='*60}")
	
	# Step 1: Extract only raw parameter promises from ESG report
	print("\n[STEP 1/3] Extracting raw parameter promises from ESG report...")
	result = find_promises(esg_report_text, json_template)
	
	# Step 2: Calculate derived metrics using paramcalculator
	print("\n[STEP 2/3] Calculating derived metrics using paramcalculator...")
	raw_params = {k: v for k, v in result.get("promise", {}).items() if k in ALL_RAW_PARAMS}
	print(f"  Found {len(raw_params)} raw parameters with values")
	result = calculate_derived_metrics(raw_params, result)
	
	# Step 3: Validate raw parameters and propagate truth to derived metrics
	print("\n[STEP 3/3] Validating raw parameters with web search...")
	result = find_truths(esg_report_text, result)
	
	# Summary
	total_promises = len([v for v in result.get("promise", {}).values() if v is not None])
	total_truths = sum(1 for v in result.get("truth", {}).values() if v)
	print(f"\n{'='*60}")
	print(f"Analysis complete for {company_name}")
	print(f"  Total promises extracted: {total_promises}")
	print(f"  Total metrics validated as TRUE: {total_truths}")
	print(f"{'='*60}\n")
	
	return result
