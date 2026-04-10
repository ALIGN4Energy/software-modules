import os
import argparse
import numpy as np
import pandas as pd
from mesa import Model, Agent
from mesa.datacollection import DataCollector


class Household(Agent):
    def __init__(self, model, household_data):
        super().__init__(model=model)
        self.model = model

        # Extract household characteristics from input data
        self.agent_id = int(household_data['Agent_id'])
        self.income = float(household_data['Income'])
        self.savings = float(household_data['Savings'])
        self.age_group = int(household_data['Age_group'])
        self.is_owner = bool(household_data['Is_owner'])
        self.has_children = bool(household_data['Has_children'])
        self.renovation_experience = bool(household_data['Renovation_experience'])
        self.education_level = int(household_data['Education_level'])
        self.female = bool(household_data['Female'])
        self.partner = bool(household_data['Partner'])
        self.energy_use = float(household_data['Energy_use'])

        self.income_category = min(10, max(0, int((self.income - 1000) / 500)))  # Income categories 0-11
        
        # Calculate technology costs from config
        self.tech_costs = {}
        for tech_name, tech_config in self.model.tech_attributes.items():
            base_cost = tech_config['base_cost']
            cost_per_unit = tech_config['cost_per_kwh_unit']
            self.tech_costs[tech_name] = base_cost + cost_per_unit * np.ceil(self.energy_use / 1000)

        # Installation status for all technologies
        self.installed_technology = None  # Tracks which technology is installed
        self.co2_saved = self.co2_produced = 0
        
        # Assign latent class based on characteristics
        self.latent_class = self._assign_latent_class()
        
        self.individual_betas = self._draw_individual_betas()
        
        # Neighbors for peer effects
        self.neighbors = []

    def _assign_latent_class(self):
        """Assign household to latent class"""
        # Class membership coefficients (from Tables 5A-8A)
        class_coefficients = {
            1: {  # Class 1 coefficients (Table 5A)
                'rental': -0.0324546,
                'renovations': -0.0443667,
                'female': 0.0522068,
                'age_25_34': 0.0581062,
                'age_35_44': 0.0943318,
                'age_45_54': 0.1068308,
                'age_55_64': 0.0975823,
                'age_65_plus': 0.0527467,
                'children': -0.0140274,
                'partner': 0.0130945,
                'netcat_1501_2000': -0.0126546,
                'netcat_2001_2500': -0.0172674,
                'netcat_2501_3000': -0.008189,
                'netcat_3001_3500': -0.0430787,
                'netcat_3501_4000': -0.0169027,
                'netcat_4001_4500': -0.0540648,
                'netcat_4501_5000': -0.0322223,
                'netcat_500_less': -0.0603413,
                'netcat_5001_7500': 0.0096021,
                'netcat_501_1000': -0.0040197,
                'netcat_7500_plus': -0.1491074,
                'netcat_no_income': 0.074928,
                'educat_1': 0.1578595,
                'educat_2': 0.0573088,
                'educat_3': 0.0873894,
                'educat_4': 0.1181394,
                'educat_5': 0.1011918,
                'educat_6': 0.1001657,
            },
            2: {  # Class 2 coefficients (Table 6A)
                'rental': 0.0431227,
                'renovations': 0.0337887,
                'female': -0.0045734,
                'age_25_34': -0.0080157,
                'age_35_44': -0.0335428,
                'age_45_54': -0.0343058,
                'age_55_64': -0.0459865,
                'age_65_plus': 0.0088797,
                'children': 0.0050348,
                'partner': 0.0053713,
                'netcat_1501_2000': -0.0270344,
                'netcat_2001_2500': 0.001556,
                'netcat_2501_3000': -0.0010818,
                'netcat_3001_3500': -0.0019144,
                'netcat_3501_4000': 0.0184151,
                'netcat_4001_4500': 0.0317078,
                'netcat_4501_5000': 0.0162533,
                'netcat_500_less': 0.2699581,
                'netcat_5001_7500': -0.0384621,
                'netcat_501_1000': -0.025238,
                'netcat_7500_plus': 0.0068332,
                'netcat_no_income': 0.0647065,
                'educat_1': -0.0387459,
                'educat_2': -0.0315783,
                'educat_3': -0.0313448,
                'educat_4': -0.0129789,
                'educat_5': -0.0089098,
                'educat_6': 0.0103483,
            },
            3: {  # Class 3 coefficients (Table 7A)
                'rental': 0.0112035,
                'renovations': -0.0622134,
                'female': 0.0396317,
                'age_25_34': 0.0373763,
                'age_35_44': 0.050491,
                'age_45_54': 0.0564306,
                'age_55_64': 0.085917,
                'age_65_plus': 0.1432253,
                'children': 0.0005696,
                'partner': 0.0221509,
                'netcat_1501_2000': 0.0234487,
                'netcat_2001_2500': 0.0100494,
                'netcat_2501_3000': 0.0033228,
                'netcat_3001_3500': 0.0149952,
                'netcat_3501_4000': 0.0030228,
                'netcat_4001_4500': -0.0069757,
                'netcat_4501_5000': 0.0221732,
                'netcat_500_less': -0.0063383,
                'netcat_5001_7500': 0.0094518,
                'netcat_501_1000': 0.0364288,
                'netcat_7500_plus': -0.0232586,
                'netcat_no_income': 0.0587847,
                'educat_1': 0.1513905,
                'educat_2': 0.0945367,
                'educat_3': -0.0202699,
                'educat_4': 0.0257524,
                'educat_5': 0.0134127,
                'educat_6': -0.0136403,
            },
            4: {  # Class 4 coefficients (Table 8A)
                'rental': -0.0218715,
                'renovations': 0.0727914,
                'female': -0.0872651,
                'age_25_34': -0.0874667,
                'age_35_44': -0.11128,
                'age_45_54': -0.1289555,
                'age_55_64': -0.1375128,
                'age_65_plus': -0.2048517,
                'children': 0.0084229,
                'partner': -0.0406166,
                'netcat_1501_2000': 0.0162403,
                'netcat_2001_2500': 0.005662,
                'netcat_2501_3000': 0.005948,
                'netcat_3001_3500': 0.0299978,
                'netcat_3501_4000': -0.0045352,
                'netcat_4001_4500': 0.0293327,
                'netcat_4501_5000': -0.0062042,
                'netcat_500_less': -0.2032786,
                'netcat_5001_7500': 0.0194081,
                'netcat_501_1000': -0.007171,
                'netcat_7500_plus': 0.1655328,
                'netcat_no_income': -0.1984192,
                'educat_1': -0.2705042,
                'educat_2': -0.1202672,
                'educat_3': -0.0357747,
                'educat_4': -0.130913,
                'educat_5': -0.1056947,
                'educat_6': -0.0968737,
            }
        }
        
        def get_income_category(income_category):
            """Map income category to coefficient"""
            income_mapping = {
                0: 'netcat_500_less',      # 0-500
                1: 'netcat_501_1000',      # 501-1000  
                2: 'netcat_1501_2000',     # 1501-2000
                3: 'netcat_2001_2500',     # 2001-2500
                4: 'netcat_2501_3000',     # 2501-3000
                5: 'netcat_3001_3500',     # 3001-3500
                6: 'netcat_3501_4000',     # 3501-4000
                7: 'netcat_4001_4500',     # 4001-4500
                8: 'netcat_4501_5000',     # 4501-5000
                9: 'netcat_5001_7500',     # 5001-7500
                10: 'netcat_7500_plus',    # >7500
                11: 'netcat_no_income'     # no income
            }
            return income_mapping.get(income_category, 'netcat_no_income')
        
        # Calculate class membership probabilities
        # Assign class/ personas
        utilities = {}
        for class_id in [1, 2, 3, 4]:
            coeff = class_coefficients[class_id]
            
            utility = coeff['rental'] * (0 if self.is_owner else 1)
            utility += coeff['renovations'] * (1 if self.renovation_experience else 0)
            utility += coeff['female'] * (1 if self.female else 0)
            utility += coeff['children'] * (1 if self.has_children else 0)
            utility += coeff['partner'] * (1 if self.partner else 0)  
            
            # Age categories
            if self.age_group == 0:  # 25-34
                utility += coeff['age_25_34']
            elif self.age_group == 1:  # 35-44
                utility += coeff['age_35_44']
            elif self.age_group == 2:  # 45-54
                utility += coeff['age_45_54']
            elif self.age_group == 3:  # 55-64
                utility += coeff['age_55_64']
            elif self.age_group == 4:  # 65+
                utility += coeff['age_65_plus']
            
            # Income categories
            income_key = get_income_category(self.income_category)
            utility += coeff[income_key]
            
            # Education categories
            if self.education_level >= 1:
                utility += coeff[f'educat_{self.education_level}']
            
            utilities[class_id] = utility
        
        # Convert to probabilities using multinomial logit
        exp_utilities = {k: np.exp(v) for k, v in utilities.items()}
        sum_exp = sum(exp_utilities.values())
        probabilities = {k: v / sum_exp for k, v in exp_utilities.items()}
        
        # Randomly assign based on probabilities
        classes = list(probabilities.keys())
        probs = list(probabilities.values())
        return np.random.choice(classes, p=probs)

    def _draw_individual_betas(self):
        """Draw individual betas"""
        
        # Betas and standard errors from Table 4A
        class_params = {
            1: {
                'cost': (-0.25312, 0.019247), # (coefficient, std_error)
                'policy_support': (0.547552, 0.123721),
                'payback_time': (-1.00502, 0.097626),
                'co2_savings': (0.619799, 0.095759),
                'comfort': (0.891001, 0.122726),
                'disruptiveness': (-0.49428, 0.076971)
            },
            2: {
                'cost': (-0.0788, 0.038897),
                'policy_support': (1.513006, 0.304419),
                'payback_time': (-0.04866, 0.068206),
                'co2_savings': (0.838051, 0.120989),
                'comfort': (0.471703, 0.096714),
                'disruptiveness': (-0.47813, 0.081666)
            },
            3: {
                'cost': (-0.01084, 0.099193),
                'policy_support': (0.256748, 0.867121),
                'payback_time': (-1.71365, 0.769812),
                'co2_savings': (-0.33795, 0.779553),
                'comfort': (-0.61454, 0.777128),
                'disruptiveness': (-0.81931, 0.465888)
            },
            4: {
                'cost': (-0.11632, 0.010712),
                'policy_support': (0.784056, 0.081604),
                'payback_time': (-0.73725, 0.042726),
                'co2_savings': (0.516491, 0.035438),
                'comfort': (1.172466, 0.0499),
                'disruptiveness': (-0.10032, 0.030099)
            }
        }
        
        params = class_params[self.latent_class]
        individual_betas = {}
        
        for attribute, (mean, se) in params.items():
            individual_betas[attribute] = np.random.normal(mean, se)
        
        return individual_betas

    def calculate_utility(self, option_attributes, peer_effect_strength=0.2):
        """Calculate utility for options using betas and peer effects"""
        
        utility = 0
        for attribute, value in option_attributes.items():
            if attribute in self.individual_betas:
                utility += self.individual_betas[attribute] * value
        
        # Add peer effect/ increases utility if neighbors have adopted this technology
        if self.neighbors:
            tech_type = option_attributes.get('technology')
            if tech_type != 'status_quo':
                peer_adoption_rate = sum(1 for n in self.neighbors if n.installed_technology == tech_type) / len(self.neighbors)
                utility += peer_effect_strength * peer_adoption_rate
        
        return utility

    def _categorize_cost_for_dcm(self, cost):
        return cost / 1000

    def _categorize_co2_for_dcm(self, co2_percentage):
        # Original DCM levels: Low (10%), Moderate (30%), High (50%)
        if co2_percentage <= 0.2:
            return 1
        elif co2_percentage <= 0.4:
            return 2
        else:
            return 3

    def _categorize_payback_for_dcm(self, years):
        # Original DCM levels: Short (5), Moderate (10), Long (20)
        if years <= 7.5:
            return 1
        elif years <= 15:
            return 2
        else:
            return 3

    def _categorize_disruptiveness_for_dcm(self, disruption_level):
        # Original DCM levels
        if disruption_level <= 1:
            return 1
        elif disruption_level <= 2:
            return 2
        else:
            return 3

    def step(self):
        """Household decision-making step"""
        self.savings += self.income * self.model.hh_savings_ratio
        
        # If already installed a technology, just update CO2
        if self.installed_technology is not None:
            self._update_co2()
            return
        
        # Prepare options for all available technologies
        tech_options = {}
        
        for tech_name, tech_config in self.model.tech_attributes.items():
            actual_cost = self.tech_costs[tech_name]
            
            # Check if policy support applies to this technology
            has_policy_support = tech_config['policy_support_available'] and self.model.policy_support
            
            tech_option = {
                'cost': self._categorize_cost_for_dcm(actual_cost),
                'policy_support': 2 if has_policy_support else 1,
                'payback_time': self._categorize_payback_for_dcm(tech_config['payback_years']),
                'co2_savings': self._categorize_co2_for_dcm(tech_config['co2_savings_pct']),
                'comfort': tech_config['comfort_level'],
                'disruptiveness': self._categorize_disruptiveness_for_dcm(tech_config['disruption_level']),
                'technology': tech_name,
                'actual_cost': actual_cost
            }
            tech_options[tech_name] = tech_option
        
        # Status quo option (no investment)
        status_quo_option = {
            'cost': 0,
            'policy_support': 0,
            'payback_time': 0,
            'co2_savings': 0,
            'comfort': 0,
            'disruptiveness': 0,
            'technology': 'status_quo'
        }
        
        # Calculate utilities for all options
        utilities = {}
        error_scale = 1.0
        
        for tech_name, tech_option in tech_options.items():
            utility = self.calculate_utility(tech_option, peer_effect_strength=self.model.peer_effect_strength)
            utility += np.random.gumbel(0, error_scale)
            
            # Apply affordability constraint
            if self.savings < tech_option['actual_cost']:
                utility = -np.inf
            
            utilities[tech_name] = utility
        
        # Status quo utility
        sq_utility = self.calculate_utility(status_quo_option, peer_effect_strength=self.model.peer_effect_strength)
        sq_utility += np.random.gumbel(0, error_scale)
        utilities['status_quo'] = sq_utility
        
        # Make decision based on highest utility
        chosen_option = max(utilities, key=utilities.get)
        
        # Install chosen technology
        if chosen_option != 'status_quo':
            self.installed_technology = chosen_option
            self.savings -= tech_options[chosen_option]['actual_cost']
        
        self._update_co2()


    def _update_co2(self):
        """Update CO2 emissions based on installed technology"""
        if self.installed_technology is None:
            # No technology installed
            self.co2_saved = 0
            self.co2_produced = self.energy_use * self.model.co2_none
        else:
            # Technology installed, use its CO2 factor
            tech_config = self.model.tech_attributes[self.installed_technology]
            co2_factor = tech_config.get('co2_factor', self.model.co2_none)
            
            if co2_factor < self.model.co2_none:
                self.co2_saved = self.energy_use * (self.model.co2_none - co2_factor)
                self.co2_produced = self.energy_use * co2_factor
            else:
                self.co2_saved = 0
                self.co2_produced = self.energy_use * co2_factor


class HeatingModel(Model):
    def __init__(self, seed: int, csv_file_path: str, tech_config_path: str = "technology_config.csv",
                 policy_support: bool = False, peer_effect_strength: float = 0.2):
        super().__init__(rng=np.random.default_rng(int(seed)))
        self.rng = np.random.default_rng(seed)

        # Model parameters
        self.policy_support = policy_support
        self.peer_effect_strength = peer_effect_strength
        self.hh_savings_ratio = 0.236 # Household savings ratio (23.6% of income)

        # Environmental parameters
        self.co2_none = 0.300  # kg CO2/kWh for current heating
        self.co2_gas = 0.250   # kg CO2/kWh for gas heating (default)
        self.co2_hp = 0.050    # kg CO2/kWh for heat pump (default)

        # Load tech_attributes
        self.tech_attributes = self._load_tech_config(tech_config_path)
        self.technology_names = list(self.tech_attributes.keys())

        # Load household data from CSV
        household_data = pd.read_csv(csv_file_path)

        # Validate schema
        household_data = self._validate_household_schema(household_data)

        # Validate and convert boolean columns
        boolean_columns = ['Is_owner', 'Has_children', 'Renovation_experience', 'Female', 'Partner']
        household_data = self._validate_and_convert_boolean_columns(household_data, boolean_columns)
        
        # Create households from CSV data
        for _, row in household_data.iterrows():
            household = Household(self, row.to_dict())
            self.agents.add(household)
        
        print(f"Created {len(self.agents)} households from CSV data.")
        print(f"Loaded {len(self.technology_names)} technologies: {', '.join(self.technology_names)}")
        
        
        # Set up neighborhood network (simple random network)
        self._setup_network()
        
        # Create dynamic model reporters
        model_reporters = {
            "step": lambda m: m.schedule.steps if hasattr(m, 'schedule') else m.datacollector.model_vars['step'][-1] + 1 if m.datacollector.model_vars['step'] else 1,
            "total_co2_saved": lambda m: sum(h.co2_saved for h in m.agents),
            "total_co2_produced": lambda m: sum(h.co2_produced for h in m.agents),
        }
        
        # Add dynamic reporters for each technology
        for tech_name in self.technology_names:
            model_reporters[f"{tech_name}_adoption"] = lambda m, tn=tech_name: sum(1 for h in m.agents if h.installed_technology == tn)
            model_reporters[f"{tech_name}_adoption_rate"] = lambda m, tn=tech_name: sum(1 for h in m.agents if h.installed_technology == tn) / len(m.agents)
        
        self.datacollector = DataCollector(
            model_reporters=model_reporters,
            agent_reporters={
                "latent_class": "latent_class",
                "installed_technology": "installed_technology",
                "age_group": "age_group",
                "income_category": "income_category",
                "is_owner": "is_owner",
                "savings": "savings",
            }
        )
        
        self.step_count = 0

    def _validate_household_schema(self, df):
        """Validate that household data has all required columns with correct types"""
        required_columns = {
            'Agent_id': ('int', 'integer identifier'),
            'Income': ('float', 'positive number'),
            'Savings': ('float', 'non-negative number'),
            'Age_group': ('int', 'integer 0-4'),
            'Is_owner': ('bool', 'boolean'),
            'Has_children': ('bool', 'boolean'),
            'Renovation_experience': ('bool', 'boolean'),
            'Education_level': ('int', 'integer 1-6'),
            'Female': ('bool', 'boolean'),
            'Partner': ('bool', 'boolean'),
            'Energy_use': ('float', 'positive number')
        }

        # Check for missing columns
        missing_columns = [col for col in required_columns.keys() if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns in household data: {', '.join(missing_columns)}.\n"
                f"Required columns: {', '.join(required_columns.keys())}\n"
                f"Available columns: {', '.join(df.columns)}"
            )

        # Validate numeric columns can be converted
        numeric_columns = {
            'Agent_id': int,
            'Income': float,
            'Savings': float,
            'Age_group': int,
            'Education_level': int,
            'Energy_use': float
        }

        for col, dtype in numeric_columns.items():
            try:
                df[col] = df[col].astype(dtype)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Column '{col}' contains invalid values that cannot be converted to {dtype.__name__}. "
                    f"Error: {e}"
                )

        # Validate value ranges
        if (df['Income'] < 0).any():
            raise ValueError("Column 'Income' contains negative values")

        if (df['Savings'] < 0).any():
            raise ValueError("Column 'Savings' contains negative values")

        if ((df['Age_group'] < 0) | (df['Age_group'] > 4)).any():
            invalid_ages = df[~df['Age_group'].between(0, 4)]['Age_group'].unique()
            raise ValueError(
                f"Column 'Age_group' must be 0-4 (0=25-34, 1=35-44, 2=45-54, 3=55-64, 4=65+). "
                f"Found invalid values: {invalid_ages}"
            )

        if ((df['Education_level'] < 1) | (df['Education_level'] > 6)).any():
            invalid_edu = df[~df['Education_level'].between(1, 6)]['Education_level'].unique()
            raise ValueError(
                f"Column 'Education_level' must be 1-6. Found invalid values: {invalid_edu}"
            )

        if (df['Energy_use'] <= 0).any():
            raise ValueError("Column 'Energy_use' must be positive (greater than 0)")

        return df

    def _validate_and_convert_boolean_columns(self, df, boolean_columns):
        """Validate and convert boolean columns with proper error handling"""
        valid_boolean_values = {
            'True': True, 'true': True, 'TRUE': True, 'T': True,
            'False': False, 'false': False, 'FALSE': False, 'F': False,
            '1': True, '0': False, 1: True, 0: False,
            True: True, False: False
        }

        for col in boolean_columns:
            if col not in df.columns:
                raise ValueError(
                    f"Required boolean column '{col}' not found in household data. "
                    f"Available columns: {', '.join(df.columns)}"
                )

            # Check for invalid values
            if df[col].dtype == 'object' or df[col].dtype == 'int64':
                unique_values = df[col].unique()
                invalid_values = [v for v in unique_values if v not in valid_boolean_values and pd.notna(v)]

                if invalid_values:
                    raise ValueError(
                        f"Invalid boolean values in column '{col}': {invalid_values}. "
                        f"Valid values are: True, False, 1, 0 (case-insensitive)"
                    )

                # Convert to boolean
                df[col] = df[col].map(valid_boolean_values)

                # Check for any NaN values that resulted from mapping
                if df[col].isna().any():
                    nan_count = df[col].isna().sum()
                    raise ValueError(
                        f"Column '{col}' has {nan_count} values that could not be converted to boolean"
                    )

        return df

    def _load_tech_config(self, tech_config_path):
        """Load technology attributes from CSV configuration file"""
        try:
            config_df = pd.read_csv(tech_config_path)
            tech_attributes = {}
            
            for _, row in config_df.iterrows():
                tech_name = row['technology']
                tech_attributes[tech_name] = {
                    'base_cost': float(row['base_cost']),
                    'cost_per_kwh_unit': float(row['cost_per_kwh_unit']),
                    'payback_years': float(row['payback_years']),
                    'co2_savings_pct': float(row['co2_savings_pct']),
                    'comfort_level': int(row['comfort_level']),
                    'disruption_level': float(row['disruption_level']),
                    'policy_support_available': bool(row['policy_support_available']),
                    'co2_factor': float(row['co2_factor'])
                }
            
            if len(tech_attributes) == 0:
                raise ValueError("No technologies found in config file")
            
            return tech_attributes
            
        except FileNotFoundError:
            print(f"Warning: Technology config file '{tech_config_path}' not found. Using default values.")
            return {
                'heat_pump': {
                    'base_cost': 6000,
                    'cost_per_kwh_unit': 500,
                    'payback_years': 10.0,
                    'co2_savings_pct': 0.5,
                    'comfort_level': 2,
                    'disruption_level': 1.5,
                    'policy_support_available': True,
                    'co2_factor': 0.050
                },
                'gas': {
                    'base_cost': 3000,
                    'cost_per_kwh_unit': 350,
                    'payback_years': 7.0,
                    'co2_savings_pct': 0.3,
                    'comfort_level': 1,
                    'disruption_level': 0.5,
                    'policy_support_available': False,
                    'co2_factor': 0.250
                }
            }

    def _setup_network(self, avg_neighbors=5):
        """Set up neighborhood network for peer effects"""
        agents = list(self.agents)
        
        for agent in agents:
            n_neighbors = np.random.poisson(avg_neighbors)
            potential_neighbors = [a for a in agents if a != agent]
            
            if len(potential_neighbors) >= n_neighbors:
                neighbors = np.random.choice(potential_neighbors, n_neighbors, replace=False)
                agent.neighbors = list(neighbors)

    def step(self):
        self.step_count += 1
        # Shuffle agents for random activation
        agents_shuffled = list(self.agents)
        self.random.shuffle(agents_shuffled)
        
        for agent in agents_shuffled:
            agent.step()
        
        self.datacollector.collect(self)

    def get_adoption_by_class(self):
        """Get adoption rates by latent class for all technologies"""
        class_adoption = {i: {'total': 0} for i in [1, 2, 3, 4]}
        
        # Initialize counters for each technology
        for tech_name in self.technology_names:
            for i in [1, 2, 3, 4]:
                class_adoption[i][tech_name] = 0
        
        # Count adoptions
        for agent in self.agents:
            class_id = agent.latent_class
            class_adoption[class_id]['total'] += 1
            if agent.installed_technology is not None:
                class_adoption[class_id][agent.installed_technology] += 1
        
        # Calculate rates
        for class_id in class_adoption:
            total = class_adoption[class_id]['total']
            if total > 0:
                for tech_name in self.technology_names:
                    rate_key = f'{tech_name}_rate'
                    class_adoption[class_id][rate_key] = class_adoption[class_id][tech_name] / total
            else:
                for tech_name in self.technology_names:
                    rate_key = f'{tech_name}_rate'
                    class_adoption[class_id][rate_key] = 0
        
        return class_adoption


def run_monte_carlo_simulation(n_runs=100, years=10, csv_file_path="tutorial_households.csv",
                               tech_config_path="tutorial_technologies.csv", policy_support=True,
                               peer_effect_strength=0.2):
    """Run Monte Carlo simulation to account for stochastic class assignment"""
    
    household_data = pd.read_csv(csv_file_path)
    n_households = len(household_data)
    
    # Get technology names from config
    config_df = pd.read_csv(tech_config_path)
    technology_names = config_df['technology'].tolist()
    
    results = []
    
    for run in range(n_runs):
        if run % 10 == 0:
            print(f"Monte Carlo run {run + 1}/{n_runs}")
        
        model = HeatingModel(seed=run, csv_file_path=csv_file_path,
                           tech_config_path=tech_config_path, policy_support=policy_support,
                           peer_effect_strength=peer_effect_strength)
        
        for year in range(years):
            model.step()
        
        adoption_by_class = model.get_adoption_by_class()
        
        # Build result dictionary dynamically
        run_result = {'run': run}
        
        # Add overall adoption rates for each technology
        for tech_name in technology_names:
            tech_total = sum(1 for h in model.agents if h.installed_technology == tech_name)
            run_result[f'{tech_name}_adoption_rate'] = tech_total / n_households
        
        # Add class-specific adoption rates
        for class_id in [1, 2, 3, 4]:
            run_result[f'class_{class_id}_size'] = adoption_by_class[class_id]['total']
            for tech_name in technology_names:
                rate_key = f'{tech_name}_rate'
                run_result[f'class_{class_id}_{tech_name}_rate'] = adoption_by_class[class_id][rate_key]
        
        results.append(run_result)
    
    return pd.DataFrame(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Run Energy Technology Adoption Agent-Based Model',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--n_runs',
        type=int,
        default=100,
        help='Number of Monte Carlo simulation runs (default: 100)'
    )

    parser.add_argument(
        '--years',
        type=int,
        default=10,
        help='Number of simulation years per run (default: 10)'
    )

    parser.add_argument(
        '--policy',
        type=str,
        default='true',
        choices=['true', 'false', 'True', 'False', '1', '0'],
        help='Enable policy support (default: true)'
    )

    parser.add_argument(
        '--peer_effect',
        type=float,
        default=0.2,
        help='Peer effect strength 0-1 (default: 0.2)'
    )

    parser.add_argument(
        '--household_data',
        type=str,
        default='tutorial_households.csv',
        help='Path to household data CSV (default: tutorial_households.csv)'
    )

    parser.add_argument(
        '--tech_config',
        type=str,
        default='tutorial_technologies.csv',
        help='Path to technology config CSV (default: tutorial_technologies.csv)'
    )

    args = parser.parse_args()

    # Convert policy string to boolean
    policy_support = args.policy.lower() in ['true', '1']

    print("Running Monte Carlo simulation...")
    print(f"Parameters: n_runs={args.n_runs}, years={args.years}, policy={policy_support}, peer_effect={args.peer_effect}")
    print(f"Data files: household_data={args.household_data}, tech_config={args.tech_config}")

    # Run Monte Carlo simulation
    mc_results = run_monte_carlo_simulation(
        n_runs=args.n_runs,
        years=args.years,
        csv_file_path=args.household_data,
        tech_config_path=args.tech_config,
        policy_support=policy_support,
        peer_effect_strength=args.peer_effect
    )

    # Get technology names from config
    config_df = pd.read_csv(args.tech_config)
    technology_names = config_df['technology'].tolist()

    # Calculate summary statistics
    print(f"\n=== MONTE CARLO RESULTS ({args.n_runs} runs) ===")
    for tech_name in technology_names:
        mean_rate = mc_results[f'{tech_name}_adoption_rate'].mean()
        std_rate = mc_results[f'{tech_name}_adoption_rate'].std()
        print(f"{tech_name.replace('_', ' ').title()} Adoption Rate: {mean_rate:.3f} ± {std_rate:.3f}")

    print("\nAdoption by Class (Mean ± Std):")
    for class_id in [1, 2, 3, 4]:
        size_mean = mc_results[f'class_{class_id}_size'].mean()
        print(f"\nClass {class_id} (avg size: {size_mean:.0f}):")
        for tech_name in technology_names:
            mean = mc_results[f'class_{class_id}_{tech_name}_rate'].mean()
            std = mc_results[f'class_{class_id}_{tech_name}_rate'].std()
            print(f"  {tech_name.replace('_', ' ').title()}: {mean:.3f}±{std:.3f}")
