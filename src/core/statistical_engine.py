"""
AMRIT StatisticalEngine - Advanced Statistical Analysis
Monte Carlo, Bayesian Inference, Benford's Law, and more
"""
import numpy as np
from scipy import stats
from scipy.special import comb
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
import random

@dataclass
class StatisticalResult:
    """Container for statistical analysis results"""
    test_name: str
    statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: Optional[float] = None
    interpretation: str = ""
    recommendations: List[str] = None

class StatisticalEngine:
    """
    Comprehensive statistical analysis engine
    Supports: Monte Carlo, Bayesian, Benford's Law, Survival Analysis
    """

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        np.random.seed(random_seed)
        random.seed(random_seed)

    # ==================== MONTE CARLO METHODS ====================

    def monte_carlo_simulation(self, 
                             model_func: Callable,
                             param_distributions: Dict[str, Callable],
                             n_iterations: int = 10000) -> Dict:
        """
        Run Monte Carlo simulation

        Args:
            model_func: Function that takes parameters and returns outcome
            param_distributions: Dict of parameter names to distribution functions
            n_iterations: Number of simulation iterations

        Returns:
            Dictionary with simulation results
        """
        results = []

        for _ in range(n_iterations):
            # Sample parameters from distributions
            params = {name: dist() for name, dist in param_distributions.items()}

            # Run model
            outcome = model_func(**params)
            results.append(outcome)

        results = np.array(results)

        return {
            "mean": np.mean(results),
            "median": np.median(results),
            "std": np.std(results),
            "ci_95": (np.percentile(results, 2.5), np.percentile(results, 97.5)),
            "min": np.min(results),
            "max": np.max(results),
            "results": results.tolist()
        }

    def monte_carlo_drug_trial(self, 
                             control_rate: float,
                             treatment_rate: float,
                             n_patients: int = 100,
                             n_simulations: int = 10000) -> Dict:
        """
        Simulate clinical trial using Monte Carlo

        Args:
            control_rate: Response rate in control group
            treatment_rate: Response rate in treatment group
            n_patients: Patients per group
            n_simulations: Number of simulations

        Returns:
            Trial simulation results
        """
        p_values = []
        effect_sizes = []

        for _ in range(n_simulations):
            # Simulate control group
            control = np.random.binomial(1, control_rate, n_patients)
            # Simulate treatment group
            treatment = np.random.binomial(1, treatment_rate, n_patients)

            # Chi-square test
            contingency = np.array([
                [np.sum(control), n_patients - np.sum(control)],
                [np.sum(treatment), n_patients - np.sum(treatment)]
            ])

            chi2, p_val, _, _ = stats.chi2_contingency(contingency)
            p_values.append(p_val)

            # Effect size (Cohen's h)
            p1 = np.mean(control)
            p2 = np.mean(treatment)
            h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
            effect_sizes.append(abs(h))

        p_values = np.array(p_values)
        effect_sizes = np.array(effect_sizes)

        power = np.mean(p_values < 0.05)

        return {
            "power": power,
            "mean_p_value": np.mean(p_values),
            "median_p_value": np.median(p_values),
            "mean_effect_size": np.mean(effect_sizes),
            "significant_trials": int(np.sum(p_values < 0.05)),
            "total_trials": n_simulations,
            "recommended_sample_size": self._calculate_sample_size(control_rate, treatment_rate, 0.8, 0.05)
        }

    def _calculate_sample_size(self, p1: float, p2: float, power: float, alpha: float) -> int:
        """Calculate required sample size for two-proportion test"""
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(power)

        p_avg = (p1 + p2) / 2
        n = (2 * p_avg * (1 - p_avg) * (z_alpha + z_beta)**2) / (p1 - p2)**2
        return int(np.ceil(n))

    # ==================== BAYESIAN METHODS ====================

    def bayesian_inference(self, 
                         prior_alpha: float, 
                         prior_beta: float,
                         successes: int,
                         trials: int) -> Dict:
        """
        Bayesian inference for binomial proportion

        Args:
            prior_alpha, prior_beta: Beta distribution parameters
            successes: Number of successes observed
            trials: Total number of trials

        Returns:
            Posterior distribution parameters and statistics
        """
        # Update with data (Beta-Binomial conjugacy)
        posterior_alpha = prior_alpha + successes
        posterior_beta = prior_beta + (trials - successes)

        # Posterior statistics
        mean = posterior_alpha / (posterior_alpha + posterior_beta)
        mode = (posterior_alpha - 1) / (posterior_alpha + posterior_beta - 2) if posterior_alpha > 1 and posterior_beta > 1 else mean
        variance = (posterior_alpha * posterior_beta) / ((posterior_alpha + posterior_beta)**2 * (posterior_alpha + posterior_beta + 1))

        # Credible intervals
        ci_95 = stats.beta.ppf([0.025, 0.975], posterior_alpha, posterior_beta)
        ci_99 = stats.beta.ppf([0.005, 0.995], posterior_alpha, posterior_beta)

        return {
            "posterior_alpha": posterior_alpha,
            "posterior_beta": posterior_beta,
            "mean": mean,
            "mode": mode,
            "variance": variance,
            "ci_95": tuple(ci_95),
            "ci_99": tuple(ci_99),
            "probability_superior": 1 - stats.beta.cdf(0.5, posterior_alpha, posterior_beta)
        }

    def bayesian_hypothesis_test(self,
                                data_group1: List[float],
                                data_group2: List[float],
                                prior_mean_diff: float = 0,
                                prior_std_diff: float = 1) -> Dict:
        """
        Bayesian two-sample test for difference in means

        Args:
            data_group1, data_group2: Data for two groups
            prior_mean_diff: Prior mean of difference
            prior_std_diff: Prior std of difference

        Returns:
            Bayesian test results
        """
        n1, n2 = len(data_group1), len(data_group2)
        mean1, mean2 = np.mean(data_group1), np.mean(data_group2)
        std1, std2 = np.std(data_group1, ddof=1), np.std(data_group2, ddof=1)

        # Pooled standard deviation
        pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1+n2-2))

        # Standard error of difference
        se_diff = pooled_std * np.sqrt(1/n1 + 1/n2)

        # Observed difference
        observed_diff = mean1 - mean2

        # Posterior for difference (assuming normal prior and normal likelihood)
        posterior_precision = 1/prior_std_diff**2 + 1/se_diff**2
        posterior_std = 1/np.sqrt(posterior_precision)
        posterior_mean = (prior_mean_diff/prior_std_diff**2 + observed_diff/se_diff**2) / posterior_precision

        # Probability that group1 > group2
        prob_greater = 1 - stats.norm.cdf(0, posterior_mean, posterior_std)

        # Bayes Factor (simplified)
        bf = np.exp((observed_diff**2) / (2 * se_diff**2))

        return {
            "posterior_mean_diff": posterior_mean,
            "posterior_std_diff": posterior_std,
            "probability_group1_greater": prob_greater,
            "bayes_factor": bf,
            "evidence_strength": self._interpret_bayes_factor(bf),
            "credible_interval_95": (
                posterior_mean - 1.96 * posterior_std,
                posterior_mean + 1.96 * posterior_std
            )
        }

    def _interpret_bayes_factor(self, bf: float) -> str:
        """Interpret Bayes Factor strength"""
        if bf < 1:
            return "Evidence for null hypothesis"
        elif bf < 3:
            return "Anecdotal evidence for alternative"
        elif bf < 10:
            return "Moderate evidence for alternative"
        elif bf < 30:
            return "Strong evidence for alternative"
        elif bf < 100:
            return "Very strong evidence for alternative"
        else:
            return "Extreme evidence for alternative"

    # ==================== BENFORD'S LAW ====================

    def benfords_law_test(self, data: List[float]) -> StatisticalResult:
        """
        Test if data follows Benford's Law
        Useful for detecting fraud in scientific data

        Args:
            data: List of numbers

        Returns:
            Statistical test result
        """
        # Extract first digits
        first_digits = []
        for num in data:
            if num != 0:
                first_digit = int(str(abs(num))[0])
                first_digits.append(first_digit)

        if not first_digits:
            return StatisticalResult(
                test_name="Benford's Law",
                statistic=0,
                p_value=1.0,
                confidence_interval=(0, 1),
                interpretation="No valid data for analysis"
            )

        # Observed frequencies
        observed = np.array([first_digits.count(d) for d in range(1, 10)])
        observed_prop = observed / len(first_digits)

        # Expected Benford's Law frequencies
        expected_prop = np.array([np.log10(1 + 1/d) for d in range(1, 10)])
        expected = expected_prop * len(first_digits)

        # Chi-square test
        chi2, p_value = stats.chisquare(observed, expected)

        # Effect size (Cramer's V)
        effect_size = np.sqrt(chi2 / (len(first_digits) * 8))

        interpretation = "Data follows Benford's Law" if p_value > 0.05 else "Data deviates from Benford's Law - potential fraud"

        recommendations = []
        if p_value <= 0.05:
            recommendations.append("Review data collection procedures")
            recommendations.append("Check for data manipulation or fabrication")
            recommendations.append("Consider independent data verification")

        return StatisticalResult(
            test_name="Benford's Law",
            statistic=chi2,
            p_value=p_value,
            confidence_interval=(0, 1),
            effect_size=effect_size,
            interpretation=interpretation,
            recommendations=recommendations or ["Data appears consistent with natural distribution"]
        )

    # ==================== SURVIVAL ANALYSIS ====================

    def kaplan_meier_estimate(self, 
                            times: List[float], 
                            events: List[int]) -> Dict:
        """
        Kaplan-Meier survival estimate

        Args:
            times: Time to event or censoring
            events: 1 if event occurred, 0 if censored

        Returns:
            Survival curve data
        """
        # Sort by time
        sorted_indices = np.argsort(times)
        times = np.array(times)[sorted_indices]
        events = np.array(events)[sorted_indices]

        unique_times = np.unique(times)
        survival_prob = []
        ci_lower = []
        ci_upper = []

        n_at_risk = len(times)
        survival = 1.0

        for t in unique_times:
            # Events at this time
            at_t = times == t
            d = np.sum(events[at_t])  # deaths
            n = np.sum(times >= t)  # at risk

            if n > 0:
                survival *= (n - d) / n

            # Greenwood's formula for CI
            if n > 0 and d > 0:
                se = survival * np.sqrt(d / (n * (n - d)))
            else:
                se = 0

            survival_prob.append(survival)
            ci_lower.append(max(0, survival - 1.96 * se))
            ci_upper.append(min(1, survival + 1.96 * se))

        return {
            "times": unique_times.tolist(),
            "survival_probabilities": survival_prob,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "median_survival": self._find_median_survival(unique_times, survival_prob)
        }

    def _find_median_survival(self, times, survival_probs):
        """Find median survival time"""
        for i, prob in enumerate(survival_probs):
            if prob <= 0.5:
                return times[i]
        return None

    # ==================== META-ANALYSIS ====================

    def meta_analysis(self, 
                     effect_sizes: List[float],
                     sample_sizes: List[int],
                     method: str = "fixed") -> Dict:
        """
        Simple meta-analysis combining effect sizes

        Args:
            effect_sizes: List of effect sizes from studies
            sample_sizes: List of sample sizes
            method: 'fixed' or 'random' effects

        Returns:
            Combined effect size and statistics
        """
        effect_sizes = np.array(effect_sizes)
        sample_sizes = np.array(sample_sizes)

        # Weights (inverse variance)
        weights = sample_sizes

        # Combined effect size
        combined_effect = np.sum(weights * effect_sizes) / np.sum(weights)

        # Standard error
        se = np.sqrt(1 / np.sum(weights))

        # Confidence interval
        ci_lower = combined_effect - 1.96 * se
        ci_upper = combined_effect + 1.96 * se

        # Heterogeneity (I^2)
        q_stat = np.sum(weights * (effect_sizes - combined_effect)**2)
        i_squared = max(0, (q_stat - (len(effect_sizes) - 1)) / q_stat * 100) if q_stat > 0 else 0

        return {
            "combined_effect_size": combined_effect,
            "standard_error": se,
            "ci_95": (ci_lower, ci_upper),
            "z_score": combined_effect / se,
            "p_value": 2 * (1 - stats.norm.cdf(abs(combined_effect / se))),
            "heterogeneity_i2": i_squared,
            "interpretation": "Significant combined effect" if abs(combined_effect / se) > 1.96 else "No significant combined effect"
        }

    # ==================== UTILITY METHODS ====================

    def calculate_power(self, 
                       effect_size: float, 
                       n: int, 
                       alpha: float = 0.05) -> float:
        """Calculate statistical power"""
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = effect_size * np.sqrt(n) - z_alpha
        return stats.norm.cdf(z_beta)

    def sample_size_calculation(self, 
                               effect_size: float, 
                               power: float = 0.8, 
                               alpha: float = 0.05) -> int:
        """Calculate required sample size"""
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(power)
        n = ((z_alpha + z_beta) / effect_size)**2
        return int(np.ceil(n))
