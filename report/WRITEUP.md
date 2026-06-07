# Minimum-Wage Effects on Food-Service Employment

## Question

Estimate the causal effect of state minimum-wage increases on county-level food-service employment using public data and quasi-experimental designs.

## Primary Design

The pre-specified primary design is a border-county-pair event study with county, year, and border-pair fixed effects. The omitted event year is -1. The scaled design should use all audited state minimum-wage changes and all Census cross-state adjacent county pairs.

## Identification

The identifying assumption is parallel counterfactual employment trends between treated and comparison border counties. The design is threatened by cross-border spillovers, contemporaneous state policies, pandemic-era disruptions, composition changes, and too few clusters in validation-only runs.

## Parallel Trends Evidence

Event-study leads:

```text
 relative_year  estimate  p_value
            -4  0.013711      NaN
            -3  0.032223      NaN
            -2  0.034328      NaN
```

Joint pre-trend diagnostic:

```text
          test    statistic      p_value  df_num  warning
joint_pretrend 7.694317e+26 2.650113e-14       3     True
```

## Main Estimates

Single-cohort validation DiD:

```text
                    estimator         term  estimate    std_error  p_value  nobs
single_cohort_border_pair_did treated:post -0.028584 6.266708e-11      0.0    90
```

Modern staggered-DiD validation output:

```text
     estimator       term  estimate    std_error      t value      p_value   ci_low  ci_high    N
pyfixest_lpdid treat_diff  0.003755 3.925231e-18 9.565309e+14 6.661338e-16 0.003755 0.003755 34.0
```

## Robustness

Synthetic-control placebo summary:

```text
 placebo_unit  post_mean_gap  pre_rmspe  post_rmspe  permutation_p_value
        34005      -0.114396   0.128918    0.114999             0.888889
        34007       0.913137   0.868473    0.913774             0.888889
        34015      -0.844928   0.975693    0.846184             0.888889
        34021       0.209496   0.276487    0.211483             0.888889
        34041      -1.706760   1.605007    1.707281             0.888889
        42017       0.085109   0.035235    0.091690             0.888889
        42045      -0.362883   0.389337    0.363441             0.888889
        42095      -0.205549   0.258625    0.206394             0.888889
        42101       1.211439   1.312119    1.213804             0.888889
```

## Phase 3: Economic Mechanisms and Heterogeneity

Phase 3 preserves the original causal design and asks whether adjustment appears through economically meaningful channels rather than only total employment.

Margin decomposition:

```text
                  outcome                        label  estimate    std_error  p_value  nobs       interpretation
           log_employment                   Employment -0.028584 6.266708e-11      0.0    90 log-point DiD effect
       log_establishments               Establishments  0.002118          NaN      NaN    90 log-point DiD effect
log_emp_per_establishment Employment per establishment -0.030702          NaN      NaN    90 log-point DiD effect
       log_avg_annual_pay           Average annual pay  0.031161          NaN      NaN    90 log-point DiD effect
```

Minimum-wage bite dose response:

```text
                  outcome        term  estimate  std_error      p_value  mean_treated_bite  nobs
           log_employment post_x_bite -0.026673   0.002756 3.696284e-22           1.048586    90
       log_establishments post_x_bite  0.003364   0.002061 1.026397e-01           1.048586    90
log_emp_per_establishment post_x_bite -0.030038   0.000694 0.000000e+00           1.048586    90
       log_avg_annual_pay post_x_bite  0.028503   0.000456 0.000000e+00           1.048586    90
```

Heterogeneity by baseline establishment scale and pre-period growth:

```text
                  outcome    heterogeneity_dimension  base_treated_post  interaction_estimate  interaction_std_error  interaction_p_value  nobs
           log_employment large_establishment_county          -0.125749              0.121457           1.282972e-14                  0.0    90
       log_establishments large_establishment_county          -0.052050              0.067710           5.825314e-15                  0.0    90
log_emp_per_establishment large_establishment_county          -0.073699              0.053747           2.779025e-15                  0.0    90
       log_avg_annual_pay large_establishment_county           0.059767             -0.035758           9.917666e-15                  0.0    90
           log_employment      high_pregrowth_county          -0.072809              0.110564           1.385356e-15                  0.0    90
       log_establishments      high_pregrowth_county          -0.022518              0.061591           1.564855e-15                  0.0    90
log_emp_per_establishment      high_pregrowth_county          -0.050291              0.048973           6.649985e-16                  0.0    90
       log_avg_annual_pay      high_pregrowth_county           0.041639             -0.026197           1.667469e-15                  0.0    90
```

Border-spillover identification status:

```text
                         test  identified                                                                                                                                            reason
control_side_border_spillover       False Validation panel contains only border controls exposed to the neighboring treated state; add interior or unexposed border controls for this test.
```

Specification curve:

```text
                  outcome             window  weighted  estimate    std_error       p_value  nobs
           log_employment               full     False -0.028584 6.266708e-11  0.000000e+00    90
           log_employment               full      True  0.002923 1.774321e-04  5.559269e-61    90
           log_employment          drop_2020     False -0.031719 1.905065e-11  0.000000e+00    80
           log_employment          drop_2020      True -0.002126 1.356222e-04  2.175725e-55    80
           log_employment balanced_2016_2022     False -0.029930 7.055194e-11  0.000000e+00    70
           log_employment balanced_2016_2022      True  0.000669 2.409212e-04  5.499037e-03    70
       log_establishments               full     False  0.002118          NaN           NaN    90
       log_establishments               full      True  0.011661 3.806112e-05  0.000000e+00    90
       log_establishments          drop_2020     False  0.002247 1.905072e-11  0.000000e+00    80
       log_establishments          drop_2020      True  0.013730 8.052939e-05  0.000000e+00    80
       log_establishments balanced_2016_2022     False  0.000869          NaN           NaN    70
       log_establishments balanced_2016_2022      True  0.006660 5.001319e-05  0.000000e+00    70
log_emp_per_establishment               full     False -0.030702          NaN           NaN    90
log_emp_per_establishment               full      True -0.008738 1.393709e-04  0.000000e+00    90
log_emp_per_establishment          drop_2020     False -0.033966          NaN           NaN    80
log_emp_per_establishment          drop_2020      True -0.015856 5.509281e-05  0.000000e+00    80
log_emp_per_establishment balanced_2016_2022     False -0.030799          NaN           NaN    70
log_emp_per_establishment balanced_2016_2022      True -0.005991 1.909080e-04 3.453087e-216    70
       log_avg_annual_pay               full     False  0.031161          NaN           NaN    90
       log_avg_annual_pay               full      True  0.028847 1.273793e-04  0.000000e+00    90
       log_avg_annual_pay          drop_2020     False  0.032980          NaN           NaN    80
       log_avg_annual_pay          drop_2020      True  0.028807 1.518602e-04  0.000000e+00    80
       log_avg_annual_pay balanced_2016_2022     False  0.030841          NaN           NaN    70
       log_avg_annual_pay balanced_2016_2022      True  0.030472 1.538085e-04  0.000000e+00    70
```

## Secondary IV

```text
                   term  estimate  std_error  p_value  nobs
endogenous_labor_demand  2.100446   0.644411 0.001116    90
```

The IV result should be interpreted only with the first-stage diagnostics in `iv_first_stage.txt`. A weak first stage is a failed robustness check, not supportive evidence.

## Limitations

The NJ/PA validation design is not a publishable full-sample estimate. It is useful for validating data cleaning and estimators, but credible inference requires the national border-county-pair panel, audited policy timing, and enough state clusters for cluster-robust or wild-bootstrap inference.

## RDD

RDD remains omitted because no genuine sharp public-data eligibility threshold has been identified.
