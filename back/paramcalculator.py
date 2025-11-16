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
    # Helper function to convert to scalar
    # ----------------------------
    @staticmethod
    def _to_scalar(value):
        """
        Attempts to convert a value to a scalar (float).
        Returns None if the value cannot be converted (e.g., string explanations).
        Returns None if the value is None.
        """
        if value is None:
            return None
        try:
            # Try to convert to float
            return float(value)
        except (ValueError, TypeError):
            # If conversion fails (e.g., string explanation), return None
            return None

    # ----------------------------
    # Derived Parameter Calculations
    # ----------------------------

    def fines_per_revenue(self):
        environmental_fines = self._to_scalar(self.environmental_fines)
        revenue = self._to_scalar(self.revenue)
        if environmental_fines is None or revenue is None or revenue == 0:
            return None
        return environmental_fines / revenue

    def fines_per_operating_site(self):
        environmental_fines = self._to_scalar(self.environmental_fines)
        operating_sites = self._to_scalar(self.operating_sites)
        if environmental_fines is None or operating_sites is None or operating_sites == 0:
            return None
        return environmental_fines / operating_sites

    def violations_per_revenue(self):
        num_violations = self._to_scalar(self.num_violations)
        revenue = self._to_scalar(self.revenue)
        if num_violations is None or revenue is None or revenue == 0:
            return None
        return num_violations / revenue

    def violations_per_operating_site(self):
        num_violations = self._to_scalar(self.num_violations)
        operating_sites = self._to_scalar(self.operating_sites)
        if num_violations is None or operating_sites is None or operating_sites == 0:
            return None
        return num_violations / operating_sites

    def violations_per_production_volume(self):
        num_violations = self._to_scalar(self.num_violations)
        production_volume = self._to_scalar(self.production_volume)
        if num_violations is None or production_volume is None or production_volume == 0:
            return None
        return num_violations / production_volume

    # Growth rate helpers
    @staticmethod
    def growth_rate(previous, current):
        previous = EnvironmentalParameters._to_scalar(previous)
        current = EnvironmentalParameters._to_scalar(current)
        if previous is None or current is None or previous == 0:
            return None
        return (current - previous) / previous

    @staticmethod
    def cagr(start, end, years):
        start = EnvironmentalParameters._to_scalar(start)
        end = EnvironmentalParameters._to_scalar(end)
        years = EnvironmentalParameters._to_scalar(years)
        if start is None or end is None or years is None or start <= 0:
            return None
        return (end / start) ** (1 / years)

    # Emissions-based derived metrics
    def emissions_intensity(self):
        ghg_emissions_scope1 = self._to_scalar(self.ghg_emissions_scope1)
        revenue = self._to_scalar(self.revenue)
        if ghg_emissions_scope1 is None or revenue is None or revenue == 0:
            return None
        return ghg_emissions_scope1 / revenue

    def emissions_per_employee(self):
        ghg_emissions_scope1 = self._to_scalar(self.ghg_emissions_scope1)
        employees = self._to_scalar(self.employees)
        if ghg_emissions_scope1 is None or employees is None or employees == 0:
            return None
        return ghg_emissions_scope1 / employees

    # Energy-related derived metrics
    def energy_intensity(self):
        energy_consumption = self._to_scalar(self.energy_consumption)
        revenue = self._to_scalar(self.revenue)
        if energy_consumption is None or revenue is None or revenue == 0:
            return None
        return energy_consumption / revenue

    def energy_efficiency_ratio(self):
        revenue = self._to_scalar(self.revenue)
        energy_consumption = self._to_scalar(self.energy_consumption)
        if revenue is None or energy_consumption is None or energy_consumption == 0:
            return None
        return revenue / energy_consumption

    def carbon_efficiency_ratio(self):
        revenue = self._to_scalar(self.revenue)
        ghg_emissions_scope1 = self._to_scalar(self.ghg_emissions_scope1)
        if revenue is None or ghg_emissions_scope1 is None or ghg_emissions_scope1 == 0:
            return None
        return revenue / ghg_emissions_scope1

    # Water-related derived metrics
    def water_intensity(self):
        water_usage = self._to_scalar(self.water_usage)
        revenue = self._to_scalar(self.revenue)
        if water_usage is None or revenue is None or revenue == 0:
            return None
        return water_usage / revenue

    def water_per_employee(self):
        water_usage = self._to_scalar(self.water_usage)
        employees = self._to_scalar(self.employees)
        if water_usage is None or employees is None or employees == 0:
            return None
        return water_usage / employees

    # Spill-related derived metrics
    def spill_frequency_per_unit(self):
        num_spills = self._to_scalar(self.num_spills)
        production_volume = self._to_scalar(self.production_volume)
        if num_spills is None or production_volume is None or production_volume == 0:
            return None
        return num_spills / production_volume

    # Generic year-over-year change
    @staticmethod
    def yoy_change(previous, current):
        previous = EnvironmentalParameters._to_scalar(previous)
        current = EnvironmentalParameters._to_scalar(current)
        if previous is None or current is None or previous == 0:
            return None
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
    # Helper function to convert to scalar
    # ----------------------------
    @staticmethod
    def _to_scalar(value):
        """
        Attempts to convert a value to a scalar (float).
        Returns None if the value cannot be converted (e.g., string explanations).
        Returns None if the value is None.
        """
        if value is None:
            return None
        try:
            # Try to convert to float
            return float(value)
        except (ValueError, TypeError):
            # If conversion fails (e.g., string explanation), return None
            return None

    # ----------------------------
    # Helper functions used in many metrics
    # ----------------------------

    @staticmethod
    def yoy_change(previous, current):
        """Year-over-year change."""
        previous = SocialParameters._to_scalar(previous)
        current = SocialParameters._to_scalar(current)
        if previous is None or current is None or previous == 0:
            return None
        return (current - previous) / previous

    @staticmethod
    def cagr(start, end, years=3):
        """General CAGR formula."""
        start = SocialParameters._to_scalar(start)
        end = SocialParameters._to_scalar(end)
        years = SocialParameters._to_scalar(years)
        if start is None or end is None or years is None or start <= 0:
            return None
        return (end / start) ** (1 / years) - 1

    @staticmethod
    def percentage_gap(a, b):
        a = SocialParameters._to_scalar(a)
        b = SocialParameters._to_scalar(b)
        if a is None or b is None:
            return None
        return a - b

    # ----------------------------
    # Derived Parameter Calculations
    # ----------------------------

    def fatalities_per_1000_employees(self):
        fatalities = self._to_scalar(self.fatalities)
        employees = self._to_scalar(self.employees)
        if fatalities is None or employees is None or employees == 0:
            return None
        return (fatalities / employees) * 1000

    def fatality_rate_trend_3yr(self, fatality_rate_3yr_ago):
        fatality_rate_3yr_ago = self._to_scalar(fatality_rate_3yr_ago)
        fatalities = self._to_scalar(self.fatalities)
        if fatality_rate_3yr_ago is None or fatalities is None:
            return None
        return self.yoy_change(fatality_rate_3yr_ago, fatalities)

    def worker_injury_rate_trend_yoy(self, prev_worker_injury_rate):
        prev_worker_injury_rate = self._to_scalar(prev_worker_injury_rate)
        worker_injury_rate = self._to_scalar(self.worker_injury_rate)
        if prev_worker_injury_rate is None or worker_injury_rate is None:
            return None
        return self.yoy_change(prev_worker_injury_rate, worker_injury_rate)

    def total_recordable_incident_rate(self):
        """
        TRIR is often defined as:
        (recordable incidents × 200,000) / total hours worked
        Here we use contractor incident rate if defined that way.
        """
        contractor_incident_rate = self._to_scalar(self.contractor_incident_rate)
        return contractor_incident_rate

    def serious_injury_frequency_rate(self):
        """
        Placeholder: depends on serious injury count.
        Could be extended if input data available.
        """
        return None

    def strikes_per_1000_employees(self):
        num_strikes = self._to_scalar(self.num_strikes)
        employees = self._to_scalar(self.employees)
        if num_strikes is None or employees is None or employees == 0:
            return None
        return (num_strikes / employees) * 1000

    def strike_frequency_trend_3yr(self, strikes_3yr_ago):
        strikes_3yr_ago = self._to_scalar(strikes_3yr_ago)
        num_strikes = self._to_scalar(self.num_strikes)
        if strikes_3yr_ago is None or num_strikes is None:
            return None
        return self.cagr(strikes_3yr_ago, num_strikes, years=3)

    def recall_growth_rate_yoy(self, prev_contractor_incident_rate):
        prev_contractor_incident_rate = self._to_scalar(prev_contractor_incident_rate)
        contractor_incident_rate = self._to_scalar(self.contractor_incident_rate)
        if prev_contractor_incident_rate is None or contractor_incident_rate is None:
            return None
        return self.yoy_change(prev_contractor_incident_rate, contractor_incident_rate)

    def glassdoor_satisfaction_trend_3yr(self, rating_3yr_ago):
        rating_3yr_ago = self._to_scalar(rating_3yr_ago)
        glassdoor_rating = self._to_scalar(self.glassdoor_rating)
        if rating_3yr_ago is None or glassdoor_rating is None:
            return None
        return self.yoy_change(rating_3yr_ago, glassdoor_rating)

    def glassdoor_ceo_approval_trend(self, prev_approval):
        prev_approval = self._to_scalar(prev_approval)
        glassdoor_ceo_approval = self._to_scalar(self.glassdoor_ceo_approval)
        if prev_approval is None or glassdoor_ceo_approval is None:
            return None
        return self.yoy_change(prev_approval, glassdoor_ceo_approval)

    def employee_engagement_proxy(self):
        """
        Combined proxy: Glassdoor rating × CEO approval rate
        CEO approval is assumed to be a % (0–100).
        """
        glassdoor_rating = self._to_scalar(self.glassdoor_rating)
        glassdoor_ceo_approval = self._to_scalar(self.glassdoor_ceo_approval)
        if glassdoor_rating is None or glassdoor_ceo_approval is None:
            return None
        return glassdoor_rating * (glassdoor_ceo_approval / 100)

    def female_workforce_ratio_trend(self, prev_female_workforce_pct):
        prev_female_workforce_pct = self._to_scalar(prev_female_workforce_pct)
        female_workforce_pct = self._to_scalar(self.female_workforce_pct)
        if prev_female_workforce_pct is None or female_workforce_pct is None:
            return None
        return self.yoy_change(prev_female_workforce_pct, female_workforce_pct)

    def female_executive_ratio_trend(self, prev_female_executive_pct):
        prev_female_executive_pct = self._to_scalar(prev_female_executive_pct)
        female_executive_pct = self._to_scalar(self.female_executive_pct)
        if prev_female_executive_pct is None or female_executive_pct is None:
            return None
        return self.yoy_change(prev_female_executive_pct, female_executive_pct)

    def gender_representation_gap(self):
        female_workforce_pct = self._to_scalar(self.female_workforce_pct)
        female_executive_pct = self._to_scalar(self.female_executive_pct)
        if female_workforce_pct is None or female_executive_pct is None:
            return None
        return self.percentage_gap(female_workforce_pct, female_executive_pct)

    def employee_turnover_trend_yoy(self, prev_turnover_pct):
        prev_turnover_pct = self._to_scalar(prev_turnover_pct)
        employee_turnover_pct = self._to_scalar(self.employee_turnover_pct)
        if prev_turnover_pct is None or employee_turnover_pct is None:
            return None
        return self.yoy_change(prev_turnover_pct, employee_turnover_pct)

    def voluntary_turnover_ratio(self, voluntary_turnover_pct):
        voluntary_turnover_pct = self._to_scalar(voluntary_turnover_pct)
        employee_turnover_pct = self._to_scalar(self.employee_turnover_pct)
        if voluntary_turnover_pct is None or employee_turnover_pct is None or employee_turnover_pct == 0:
            return None
        return voluntary_turnover_pct / employee_turnover_pct

    def retention_stability_index(self):
        """Inverse of turnover (higher = more stable)."""
        employee_turnover_pct = self._to_scalar(self.employee_turnover_pct)
        if employee_turnover_pct is None:
            return None
        return 1 - (employee_turnover_pct / 100)

    def high_performer_turnover_estimate(self, prev_high_perf_turnover, curr_high_perf_turnover):
        prev_high_perf_turnover = self._to_scalar(prev_high_perf_turnover)
        curr_high_perf_turnover = self._to_scalar(curr_high_perf_turnover)
        if prev_high_perf_turnover is None or curr_high_perf_turnover is None:
            return None
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
    # Helper function to convert to scalar
    # -----------------------
    @staticmethod
    def _to_scalar(value):
        """
        Attempts to convert a value to a scalar (float).
        Returns None if the value cannot be converted (e.g., string explanations).
        Returns None if the value is None.
        """
        if value is None:
            return None
        try:
            # Try to convert to float
            return float(value)
        except (ValueError, TypeError):
            # If conversion fails (e.g., string explanation), return None
            return None

    # -----------------------
    # Helper functions
    # -----------------------

    @staticmethod
    def yoy_change(previous, current):
        previous = GovernanceParameters._to_scalar(previous)
        current = GovernanceParameters._to_scalar(current)
        if previous is None or current is None or previous == 0:
            return None
        return (current - previous) / previous

    @staticmethod
    def cagr(start, end, years=3):
        start = GovernanceParameters._to_scalar(start)
        end = GovernanceParameters._to_scalar(end)
        years = GovernanceParameters._to_scalar(years)
        if start is None or end is None or years is None or start <= 0:
            return None
        return (end / start) ** (1 / years) - 1

    # -----------------------
    # Derived parameters
    # -----------------------

    def lawsuits_per_revenue(self):
        num_lawsuits = self._to_scalar(self.num_lawsuits)
        revenue = self._to_scalar(self.revenue)
        if num_lawsuits is None or revenue is None or revenue == 0:
            return None
        return num_lawsuits / revenue

    def lawsuit_growth_rate(self, previous_lawsuits):
        previous_lawsuits = self._to_scalar(previous_lawsuits)
        num_lawsuits = self._to_scalar(self.num_lawsuits)
        if previous_lawsuits is None or num_lawsuits is None:
            return None
        return self.yoy_change(previous_lawsuits, num_lawsuits)

    def average_lawsuit_severity(self, total_lawsuit_costs):
        total_lawsuit_costs = self._to_scalar(total_lawsuit_costs)
        num_lawsuits = self._to_scalar(self.num_lawsuits)
        if total_lawsuit_costs is None or num_lawsuits is None or num_lawsuits == 0:
            return None
        return total_lawsuit_costs / num_lawsuits

    def lawsuits_per_operating_country(self):
        num_lawsuits = self._to_scalar(self.num_lawsuits)
        operating_countries = self._to_scalar(self.operating_countries)
        if num_lawsuits is None or operating_countries is None or operating_countries == 0:
            return None
        return num_lawsuits / operating_countries

    def regulatory_investigations_per_revenue(self):
        regulatory_investigations = self._to_scalar(self.regulatory_investigations)
        revenue = self._to_scalar(self.revenue)
        if regulatory_investigations is None or revenue is None or revenue == 0:
            return None
        return regulatory_investigations / revenue

    def regulatory_investigation_growth_rate(self, previous_investigations):
        previous_investigations = self._to_scalar(previous_investigations)
        regulatory_investigations = self._to_scalar(self.regulatory_investigations)
        if previous_investigations is None or regulatory_investigations is None:
            return None
        return self.yoy_change(previous_investigations, regulatory_investigations)

    def regulatory_investigation_duration(self):
        """Assumes average investigation length is provided externally."""
        avg_reg_investigation_length = self._to_scalar(self.avg_reg_investigation_length)
        return avg_reg_investigation_length

    def corruption_cases_per_billion_revenue(self):
        corruption_cases = self._to_scalar(self.corruption_cases)
        revenue = self._to_scalar(self.revenue)
        if corruption_cases is None or revenue is None or revenue == 0:
            return None
        return corruption_cases / (revenue / 1_000_000_000)

    def corruption_case_growth_rate(self, previous_cases):
        previous_cases = self._to_scalar(previous_cases)
        corruption_cases = self._to_scalar(self.corruption_cases)
        if previous_cases is None or corruption_cases is None:
            return None
        return self.yoy_change(previous_cases, corruption_cases)

    def corruption_severity_score(self):
        """Total fines per corruption case."""
        corruption_total_fines = self._to_scalar(self.corruption_total_fines)
        corruption_cases = self._to_scalar(self.corruption_cases)
        if corruption_total_fines is None or corruption_cases is None or corruption_cases == 0:
            return None
        return corruption_total_fines / corruption_cases

    def anti_competitive_fines_per_revenue(self):
        anti_competitive_fines = self._to_scalar(self.anti_competitive_fines)
        revenue = self._to_scalar(self.revenue)
        if anti_competitive_fines is None or revenue is None or revenue == 0:
            return None
        return anti_competitive_fines / revenue

    def anti_competitive_fines_growth_rate(self, previous_fines):
        previous_fines = self._to_scalar(previous_fines)
        anti_competitive_fines = self._to_scalar(self.anti_competitive_fines)
        if previous_fines is None or anti_competitive_fines is None:
            return None
        return self.yoy_change(previous_fines, anti_competitive_fines)

    def anti_competitive_violations_per_country(self):
        anti_competitive_fines = self._to_scalar(self.anti_competitive_fines)
        operating_countries = self._to_scalar(self.operating_countries)
        if anti_competitive_fines is None or operating_countries is None or operating_countries == 0:
            return None
        return anti_competitive_fines / operating_countries

    def board_independence_trend_3yr(self, independence_pct_3yr_ago):
        independence_pct_3yr_ago = self._to_scalar(independence_pct_3yr_ago)
        board_independence_pct = self._to_scalar(self.board_independence_pct)
        if independence_pct_3yr_ago is None or board_independence_pct is None:
            return None
        return self.yoy_change(independence_pct_3yr_ago, board_independence_pct)

    def independent_directors_ratio(self):
        board_independence_pct = self._to_scalar(self.board_independence_pct)
        if board_independence_pct is None:
            return None
        return board_independence_pct / 100

    def financial_restatements_per_year(self, years=1):
        financial_restatements = self._to_scalar(self.financial_restatements)
        years = self._to_scalar(years)
        if financial_restatements is None or years is None or years == 0:
            return None
        return financial_restatements / years

    def restatement_severity_score(self, earnings_impact):
        """Impact on earnings per restatement."""
        earnings_impact = self._to_scalar(earnings_impact)
        financial_restatements = self._to_scalar(self.financial_restatements)
        if earnings_impact is None or financial_restatements is None or financial_restatements == 0:
            return None
        return earnings_impact / financial_restatements

    def csuite_turnover_frequency(self):
        csuite_turnover_rate = self._to_scalar(self.csuite_turnover_rate)
        return csuite_turnover_rate

    def csuite_turnover_spike_indicator(self, previous_turnover_rate, threshold=0.2):
        """Returns True if YoY turnover increase > threshold."""
        previous_turnover_rate = self._to_scalar(previous_turnover_rate)
        csuite_turnover_rate = self._to_scalar(self.csuite_turnover_rate)
        if previous_turnover_rate is None or csuite_turnover_rate is None:
            return None
        change = self.yoy_change(previous_turnover_rate, csuite_turnover_rate)
        return change is not None and change > threshold

    def ceo_tenure_length(self):
        ceo_tenure_years = self._to_scalar(self.ceo_tenure_years)
        return ceo_tenure_years

    def executive_stability_index(self):
        """Inverse of turnover."""
        csuite_turnover_rate = self._to_scalar(self.csuite_turnover_rate)
        if csuite_turnover_rate is None:
            return None
        return 1 - (csuite_turnover_rate / 100)

    def political_donations_per_revenue(self):
        political_donations = self._to_scalar(self.political_donations)
        revenue = self._to_scalar(self.revenue)
        if political_donations is None or revenue is None or revenue == 0:
            return None
        return political_donations / revenue

    def political_donations_concentration(self, top_sector_pct):
        """Returns % of political donations going to top sector/party."""
        top_sector_pct = self._to_scalar(top_sector_pct)
        return top_sector_pct

    def political_donation_volatility_yoy(self, previous_donations):
        previous_donations = self._to_scalar(previous_donations)
        political_donations = self._to_scalar(self.political_donations)
        if previous_donations is None or political_donations is None:
            return None
        return self.yoy_change(previous_donations, political_donations)

    def major_shareholder_lawsuits_per_billion_revenue(self):
        major_shareholder_lawsuits = self._to_scalar(self.major_shareholder_lawsuits)
        revenue = self._to_scalar(self.revenue)
        if major_shareholder_lawsuits is None or revenue is None or revenue == 0:
            return None
        return major_shareholder_lawsuits / (revenue / 1_000_000_000)
