# E04-P2: factor attribution specification

Registered September 17, 2026 before viewing attribution results. E04-P1's performance is already known; this freezes a subsequent diagnostic, not untouched strategy discovery. No strategy or selection parameters change.

Inputs: January 2000–December 2025 P1 monthly returns, 312 complete months. Primary cost: 10 bp under P1's proportional target-weight approximation; 0 and 25 bp are descriptive sensitivities. Require the original industry raw-file SHA-256 and reproduction of committed P1 aggregate statistics before interpreting this diagnostic.

Download official monthly [Fama–French five factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip) and [Momentum](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip). Preserve raw ZIPs, SHA-256, retrieval times, source headers and code/dependency versions. Join by YYYYMM; reject missing/duplicate/nonconsecutive months, missing sentinels, nonfinite values and changed schemas. Percentages become decimals.

Model: strategy return minus benchmark return = constant + beta_M × Mkt-RF + beta_S × SMB + beta_H × HML + beta_R × RMW + beta_C × CMA + beta_U × Mom + residual. Use FF5's SMB. Do not subtract RF from active returns. Six factors plus an intercept, ordinary least squares, all contemporaneous.

Inference: Newey–West covariance, Bartlett weights 1−lag/13 for lags 1 through 12, finite-sample multiplier n/(n−7), normal 95% interval with z=1.959963984540054. Annualized arithmetic alpha and its interval = monthly values ×12, not compounding. Betas remain unannualized. Report all coefficients and robust standard errors, R-squared, rank/conditioning, residual mean/lag-1 correlation and mean decomposition. Fail on deficient rank. Cross-check OLS and covariance with statsmodels.

Correctness tests: known-coefficient recovery; manual HAC against statsmodels; lag-zero covariance versus HC1; zero-active handling; factor-column permutation; percent/decimal scaling; calendar and unit checks; malformed factor files; annualization; unchanged P1 reconstruction. All sensitivities use identical dates/factors. No search over factors, lags, cutoffs or sample periods.

Interpretation: contemporaneous conditional attribution, not forecasting or causality. Constant exposures can omit changing betas and omitted factors. Mom is stock-level momentum, not a direct industry factor. Even a significant intercept would not establish an executable edge in ETFs or the liquid-stock universe.

Source definitions: [FF5](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html), [Momentum](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html). Historical series can be reconstructed and revised; retain the actual downloaded vintage.
