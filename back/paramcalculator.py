class EnvironmentalParameters:
    def __init__(
        self,
        environmental_fines,
        num_violations,
        num_spills,
        ghg_emissions_direct,
        ghg_emissions_scope1,
        energy_consumption,
        water_usage,
        active_lawsuits,
        environmental_certifications,
        # Additional data needed for derived metrics
        revenue,
        operating_sites,
        production_volume,
        employees
    ):
        # Raw parameters
        self.environmental_fines = environmental_fines
        self.num_violations = num_violations
        self.num_spills = num_spills
        self.ghg_emissions_direct = ghg_emissions_direct
        self.ghg_emissions_scope1 = ghg_emissions_scope1
        self.energy_consumption = energy_consumption
        self.water_usage = water_usage
        self.active_lawsuits = active_lawsuits
        self.environmental_certifications = environmental_certifications

        # Additional required parameters
        self.revenue = revenue
        self.operating_sites = operating_sites
        self.production_volume = production_volume
        self.employees = employees

    # ----------------------------
    # Derived Parameter Calculations
    # ----------------------------

    def fines_per_revenue(self):
        return self.environmental_fines / self.revenue

    def fines_per_operating_site(self):
        return self.environmental_fines / self.operating_sites

    def violations_per_revenue(self):
        return self.num_violations / self.revenue

    def violations_per_operating_site(self):
        return self.num_violations / self.operating_sites

    def violations_per_production_volume(self):
        return self.num_violations / self.production_volume

    # Growth rate helpers
    @staticmethod
    def growth_rate(previous, current):
        return (current - previous) / previous

    @staticmethod
    def cagr(start, end, years):
        return (end / start) ** (1 / years) if start > 0 else None

    # Emissions-based derived metrics
    def emissions_intensity(self):
        return self.ghg_emissions_scope1 / self.revenue

    def emissions_per_employee(self):
        return self.ghg_emissions_scope1 / self.employees

    # Energy-related derived metrics
    def energy_intensity(self):
        return self.energy_consumption / self.revenue

    def energy_efficiency_ratio(self):
        return self.revenue / self.energy_consumption

    def carbon_efficiency_ratio(self):
        return self.revenue / self.ghg_emissions_scope1

    # Water-related derived metrics
    def water_intensity(self):
        return self.water_usage / self.revenue

    def water_per_employee(self):
        return self.water_usage / self.employees

    # Spill-related derived metrics
    def spill_frequency_per_unit(self):
        return self.num_spills / self.production_volume

    # Generic year-over-year change
    @staticmethod
    def yoy_change(previous, current):
        return (current - previous) / previous

class SocialParameters:
    def __init__(
        self,
        fatalities,
        worker_injury_rate,
        num_strikes,
        contractor_incident_rate,
        glassdoor_rating,
        glassdoor_ceo_approval,
        female_workforce_pct,
        female_executive_pct,
        employee_turnover_pct,
        # Additional inputs required for derived calculations
        employees
    ):
        # Raw social parameters
        self.fatalities = fatalities
        self.worker_injury_rate = worker_injury_rate
        self.num_strikes = num_strikes
        self.contractor_incident_rate = contractor_incident_rate
        self.glassdoor_rating = glassdoor_rating
        self.glassdoor_ceo_approval = glassdoor_ceo_approval
        self.female_workforce_pct = female_workforce_pct
        self.female_executive_pct = female_executive_pct
        self.employee_turnover_pct = employee_turnover_pct

        # Supporting values
        self.employees = employees

    # ----------------------------
    # Helper functions used in many metrics
    # ----------------------------

    @staticmethod
    def yoy_change(previous, current):
        """Year-over-year change."""
        return (current - previous) / previous if previous else None

    @staticmethod
    def cagr(start, end, years=3):
        """General CAGR formula."""
        return (end / start) ** (1 / years) - 1 if start > 0 else None

    @staticmethod
    def percentage_gap(a, b):
        return a - b

    # ----------------------------
    # Derived Parameter Calculations
    # ----------------------------

    def fatalities_per_1000_employees(self):
        return (self.fatalities / self.employees) * 1000

    def fatality_rate_trend_3yr(self, fatality_rate_3yr_ago):
        return self.yoy_change(fatality_rate_3yr_ago, self.fatalities)

    def worker_injury_rate_trend_yoy(self, prev_worker_injury_rate):
        return self.yoy_change(prev_worker_injury_rate, self.worker_injury_rate)

    def total_recordable_incident_rate(self):
        """
        TRIR is often defined as:
        (recordable incidents × 200,000) / total hours worked
        Here we use contractor incident rate if defined that way.
        """
        return self.contractor_incident_rate

    def serious_injury_frequency_rate(self):
        """
        Placeholder: depends on serious injury count.
        Could be extended if input data available.
        """
        return None

    def strikes_per_1000_employees(self):
        return (self.num_strikes / self.employees) * 1000

    def strike_frequency_trend_3yr(self, strikes_3yr_ago):
        return self.cagr(strikes_3yr_ago, self.num_strikes, years=3)

    def recall_growth_rate_yoy(self, prev_contractor_incident_rate):
        return self.yoy_change(prev_contractor_incident_rate, self.contractor_incident_rate)

    def glassdoor_satisfaction_trend_3yr(self, rating_3yr_ago):
        return self.yoy_change(rating_3yr_ago, self.glassdoor_rating)

    def glassdoor_ceo_approval_trend(self, prev_approval):
        return self.yoy_change(prev_approval, self.glassdoor_ceo_approval)

    def employee_engagement_proxy(self):
        """
        Combined proxy: Glassdoor rating × CEO approval rate
        CEO approval is assumed to be a % (0–100).
        """
        return self.glassdoor_rating * (self.glassdoor_ceo_approval / 100)

    def female_workforce_ratio_trend(self, prev_female_workforce_pct):
        return self.yoy_change(prev_female_workforce_pct, self.female_workforce_pct)

    def female_executive_ratio_trend(self, prev_female_executive_pct):
        return self.yoy_change(prev_female_executive_pct, self.female_executive_pct)

    def gender_representation_gap(self):
        return self.percentage_gap(self.female_workforce_pct, self.female_executive_pct)

    def employee_turnover_trend_yoy(self, prev_turnover_pct):
        return self.yoy_change(prev_turnover_pct, self.employee_turnover_pct)

    def voluntary_turnover_ratio(self, voluntary_turnover_pct):
        return voluntary_turnover_pct / self.employee_turnover_pct

    def retention_stability_index(self):
        """Inverse of turnover (higher = more stable)."""
        return 1 - (self.employee_turnover_pct / 100)

    def high_performer_turnover_estimate(self, prev_high_perf_turnover, curr_high_perf_turnover):
        return self.yoy_change(prev_high_perf_turnover, curr_high_perf_turnover)
    
class GovernanceParameters:
    def __init__(
        self,
        num_lawsuits,
        regulatory_investigations,
        corruption_cases,
        anti_competitive_fines,
        board_independence_pct,
        financial_restatements,
        csuite_turnover_rate,
        political_donations,
        major_shareholder_lawsuits,
        # Additional needed inputs
        revenue,
        operating_countries,
        corruption_total_fines=None,  # if available
        avg_reg_investigation_length=None,
        ceo_tenure_years=None
    ):
        # Raw parameters
        self.num_lawsuits = num_lawsuits
        self.regulatory_investigations = regulatory_investigations
        self.corruption_cases = corruption_cases
        self.anti_competitive_fines = anti_competitive_fines
        self.board_independence_pct = board_independence_pct
        self.financial_restatements = financial_restatements
        self.csuite_turnover_rate = csuite_turnover_rate
        self.political_donations = political_donations
        self.major_shareholder_lawsuits = major_shareholder_lawsuits

        # Additional inputs for derived values
        self.revenue = revenue
        self.operating_countries = operating_countries
        self.corruption_total_fines = corruption_total_fines
        self.avg_reg_investigation_length = avg_reg_investigation_length
        self.ceo_tenure_years = ceo_tenure_years

    # -----------------------
    # Helper functions
    # -----------------------

    @staticmethod
    def yoy_change(previous, current):
        return (current - previous) / previous if previous else None

    @staticmethod
    def cagr(start, end, years=3):
        return (end / start) ** (1 / years) - 1 if start > 0 else None

    # -----------------------
    # Derived parameters
    # -----------------------

    def lawsuits_per_revenue(self):
        return self.num_lawsuits / self.revenue

    def lawsuit_growth_rate(self, previous_lawsuits):
        return self.yoy_change(previous_lawsuits, self.num_lawsuits)

    def average_lawsuit_severity(self, total_lawsuit_costs):
        return total_lawsuit_costs / self.num_lawsuits if self.num_lawsuits else None

    def lawsuits_per_operating_country(self):
        return self.num_lawsuits / self.operating_countries

    def regulatory_investigations_per_revenue(self):
        return self.regulatory_investigations / self.revenue

    def regulatory_investigation_growth_rate(self, previous_investigations):
        return self.yoy_change(previous_investigations, self.regulatory_investigations)

    def regulatory_investigation_duration(self):
        """Assumes average investigation length is provided externally."""
        return self.avg_reg_investigation_length

    def corruption_cases_per_billion_revenue(self):
        return self.corruption_cases / (self.revenue / 1_000_000_000)

    def corruption_case_growth_rate(self, previous_cases):
        return self.yoy_change(previous_cases, self.corruption_cases)

    def corruption_severity_score(self):
        """Total fines per corruption case."""
        if self.corruption_total_fines is None or self.corruption_cases == 0:
            return None
        return self.corruption_total_fines / self.corruption_cases

    def anti_competitive_fines_per_revenue(self):
        return self.anti_competitive_fines / self.revenue

    def anti_competitive_fines_growth_rate(self, previous_fines):
        return self.yoy_change(previous_fines, self.anti_competitive_fines)

    def anti_competitive_violations_per_country(self):
        return self.anti_competitive_fines / self.operating_countries

    def board_independence_trend_3yr(self, independence_pct_3yr_ago):
        return self.yoy_change(independence_pct_3yr_ago, self.board_independence_pct)

    def independent_directors_ratio(self):
        return self.board_independence_pct / 100

    def financial_restatements_per_year(self, years=1):
        return self.financial_restatements / years

    def restatement_severity_score(self, earnings_impact):
        """Impact on earnings per restatement."""
        return earnings_impact / self.financial_restatements if self.financial_restatements else None

    def csuite_turnover_frequency(self):
        return self.csuite_turnover_rate

    def csuite_turnover_spike_indicator(self, previous_turnover_rate, threshold=0.2):
        """Returns True if YoY turnover increase > threshold."""
        change = self.yoy_change(previous_turnover_rate, self.csuite_turnover_rate)
        return change is not None and change > threshold

    def ceo_tenure_length(self):
        return self.ceo_tenure_years

    def executive_stability_index(self):
        """Inverse of turnover."""
        return 1 - (self.csuite_turnover_rate / 100)

    def political_donations_per_revenue(self):
        return self.political_donations / self.revenue

    def political_donations_concentration(self, top_sector_pct):
        """Returns % of political donations going to top sector/party."""
        return top_sector_pct

    def political_donation_volatility_yoy(self, previous_donations):
        return self.yoy_change(previous_donations, self.political_donations)

    def major_shareholder_lawsuits_per_billion_revenue(self):
        return self.major_shareholder_lawsuits / (self.revenue / 1_000_000_000)
