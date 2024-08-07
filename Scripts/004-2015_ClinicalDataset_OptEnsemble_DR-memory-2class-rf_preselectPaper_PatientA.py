"""
==============================================================
All datasets - evaluation - FUCONE
===============================================================
"""
# Authors: Sylvain Chevallier <sylvain.chevallier@uvsq.fr>,
#          Marie-Constance Corsi <marie.constance.corsi@gmail.com>
#
# License: BSD (3-clause)
import os.path as osp
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
import pickle
import gzip
import warnings

from sklearn.base import clone
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.ensemble import StackingClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import (
    LogisticRegression,
)
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

from pyriemann.spatialfilters import CSP
from pyriemann.tangentspace import TangentSpace
from pyriemann.classification import MDM, FgMDM


from moabb.datasets import (
    BNCI2015004,  # rf
)
from moabb.paradigms import MotorImagery
from moabb.pipelines.csp import TRCSP

from fc_pipeline import (
    FunctionalTransformer,
    EnsureSPD,
    FC_DimRed,
    GetDataMemory,
)

warnings.filterwarnings(action='ignore', category=ConvergenceWarning)

##
if os.path.basename(os.getcwd()) == "FUCONE":
    os.chdir("Database")
basedir = os.getcwd()

datasets = [BNCI2015004()]


spectral_met = ["cov", "imcoh", "instantaneous"]  
print(
    "#################" + "\n"
    "List of pre-selected FC metrics: " + "\n" + str(spectral_met) + "\n"
    "#################"
)
freqbands = {"defaultBand": [8, 35]}
print(
    "#################" + "\n"
    "List of pre-selected Frequency bands: " + "\n" + str(freqbands) + "\n"
    "#################"
)
# events = ["left_hand", "right_hand", "feet", "rest"]
events = ["right_hand", "feet"]
print(
    "#################" + "\n"
    "List of selected events: " + "\n" + str(events) + "\n"
    "#################"
)
threshold = [0.05]
percent_nodes = [10, 20, 30]

## Baseline evaluations
bs_fmin, bs_fmax = 8, 35
ft = FunctionalTransformer(delta=1, ratio=0.5, method="cov", fmin=bs_fmin, fmax=bs_fmax)
step_trcsp = [("trcsp", TRCSP(nfilter=6)), ("lda", LDA())]
step_regcsp = [
    ("csp", CSP(nfilter=6)),
    ("lda", LDA(solver="lsqr", shrinkage="auto")),
]
step_csp = [
    ("csp", CSP(nfilter=6)),
    (
        "optsvm",
        GridSearchCV(SVC(), {"kernel": ("linear", "rbf"), "C": [0.1, 1, 10]}, cv=3),
    ),
]
step_mdm = [("fgmdm", FgMDM(metric="riemann", tsupdate=False))]
step_cov = [
    ("tg", TangentSpace(metric="riemann")),
    (
        "LogistReg",
        LogisticRegression(
            penalty="elasticnet", l1_ratio=0.15, intercept_scaling=1000.0, solver="saga"
        ),
    ),
]
step_fc = [
    ("tg", TangentSpace(metric="riemann")),
    (
        "LogistReg",
        LogisticRegression(
            penalty="elasticnet", l1_ratio=0.15, intercept_scaling=1000.0, solver="saga"
        ),
    ),
]
## Specific list of channels definition, cf in the paper, some of them wer noisy: https://storage.googleapis.com/plos-corpus-prod/10.1371/journal.pone.0123727/1/pone.0123727.pdf?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=wombat-sa%40plos-prod.iam.gserviceaccount.com%2F20210906%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20210906T105642Z&X-Goog-Expires=86400&X-Goog-SignedHeaders=host&X-Goog-Signature=49275c216ee41ee40065153512faafae7be2c1e3a9995f095af3bd7f0c65047f30a24f757c551253d54343a352598b9301986627bddfa4cb2b0da4953064736e0775906fd6820f61420ce852d039f3e0f1ca431500204ce26f07c94c2f93da267a6c8b82dcb380a137902a9c5438823e691d381727b6c3840f602005fce507f18a4626e9e5aed7fcd66d29a9d9a53fad4229708a92075856623ec4306c40efd8680f74ed386896dd1510a94970390581430a40e930200195a51eeaebc31d561e8110b34bc0cb68c640b56879cd6faab94e7f02c8f3b7e51fe6d82ed06b6545a71ebf50ebbb0fba32c96f8f28097b248f885390a13a33889d0174b0370268183f
dict_list_chann=dict()
# Patient A, considered here
dict_list_chann["1"]=[#'AFz', 'F7',
                      'F3', 'Fz', 'F4', 'F8', 'FC3', 'FCz', 'FC4',
                      #'T3',
                      'C3', 'Cz', 'C4', 
                    # 'T4',  - impossible to find a layout with T4...
                    'CP3', 'CPz', 'CP4',
                      #'P7',
                      'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8', 'PO3', 'PO4', 'O1', 'O2']

dict_list_chann["2"]=[#'AFz', 'F7',
                      'F3', 'Fz', 'F4', 'F8', 'FC3', 'FCz', 'FC4', 'T3', 'C3', 'Cz', 'C4',
                      #'T4',
                      'CP3', 'CPz', 'CP4', 'P7', 'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8',
                      #'PO3',
                      'PO4',
                      #'O1',
                      'O2']

dict_list_chann["3"]=[#'AFz', 'F7',
                      'F3', 'Fz', 'F4', 'F8', 'FC3', 'FCz', 'FC4', 'T3', 'C3', 'Cz', 'C4', 'T4',
                      'CP3', 'CPz', 'CP4', 'P7', 'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8', 'PO3',
                      #'PO4',
                      'O1', 'O2']

dict_list_chann["4"]=[#'AFz', 'F7',
                      'F3', 'Fz', 'F4', 'F8', 'FC3', 'FCz', 'FC4',
                      #'T3',
                      'C3', 'Cz', 'C4',
                      #'T4',
                      'CP3', 'CPz', 'CP4',
                      #'P7',
                      'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6',
                      #'P8',
                      'PO3',
                      #'PO4',
                      'O1', 'O2']

dict_list_chann["5"]=['AFz',
                      #'F7',
                      'F3', 'Fz', 'F4', 'F8', 'FC3', 'FCz', 'FC4',
                      #'T3',
                      'C3', 'Cz', 'C4',  'T4', 'CP3', 'CPz', 'CP4', 'P7',
                      'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8', 'PO3', 'PO4', 'O1', 'O2']

dict_list_chann["6"]=['AFz',
                      #'F7',
                      'F3', 'Fz', 'F4', 'F8', 'FC3', 'FCz', 'FC4', 'T3', 'C3', 'Cz',
                      #'C4',
                      'T4', 'CP3', 'CPz', 'CP4', 'P7', 'P5', 'P3', 'P1', 'Pz', 'P2', 'P4',
                      #'P6',
                      'P8', 'PO3', 'PO4', 'O1', 'O2']

dict_list_chann["7"]=[#'AFz', 'F7',
                      'F3', 'Fz', 'F4', 'F8', 'FC3', 'FCz', 'FC4',
                      #'T3',
                      'C3', 'Cz', 'C4', 'T4',
                      'CP3', 'CPz', 'CP4',
                      #'P7',
                      'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8', 'PO3', 'PO4', 'O1', 'O2']

dict_list_chann["8"]=[#'AFz', 'F7',
                    'F3', 'Fz',
                    #'F4',
                    'F8',
                    #'FC3',
                    'FCz',
                    #'FC4',
                    'T3', 'C3', 'Cz', 'C4',
                    # 'T4',
                    'CP3', 'CPz', 'CP4',
                    #'P7',
                    'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6',
                    #'P8',
                    'PO3', 'PO4', 'O1', 'O2']

dict_list_chann["9"]=[#'AFz', 'F7',
                     'F3', 'Fz', 'F4', 'F8', 'FC3', 'FCz', 'FC4',
                     #'T3',
                     'C3', 'Cz', 'C4',
                     #'T4',
                    'CP3', 'CPz', 'CP4', 'P7', 'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8', 'PO3', 'PO4', 'O1', 'O2']

## Specific evaluation for ensemble learning
for d in datasets:
    subj = d.subject_list[:2]  # we work only with patient A here
    path_csv_root = basedir + "/1_Dataset-csv/" + d.code.replace(" ", "-")
    if not osp.exists(path_csv_root):
        os.mkdir(path_csv_root)
    path_data_root = basedir + "/2_Dataset-npz/" + d.code.replace(" ", "-")
    if not osp.exists(path_data_root):
        os.mkdir(path_data_root)
    path_data_root_chan = path_data_root + "/Chan_select/"
    path_figures_root = basedir + "/0_Figures/" + d.code.replace(" ", "-")

    # precompute all metrics for datasets
    print("\n\n\n#################\nPrecompute all metrics\n#################")
    precomp_name = path_data_root + f"/allsubject-metrics-{len(events)}classes.gz"
    if osp.exists(precomp_name):
        print("Loading existing precomputations")
        with gzip.open(precomp_name, "r") as f:
            data_fc = pickle.load(f)
    else:
        data_fc = {}
        for f in freqbands:
            fmin = freqbands[f][0]
            fmax = freqbands[f][1]
            subjects = subj
            data_fc[f] = {}
            for subject in tqdm(subjects, desc="subject"):
                list_chann=dict_list_chann[str(subject)]
                data_fc[f][subject] = {}
                # paradigm = LeftRightImagery(fmin=fmin, fmax=fmax)
                paradigm = MotorImagery(events=events, n_classes=len(events), fmin=fmin, fmax=fmax, channels=list_chann)
                ep_, _, _ = paradigm.get_data(
                    dataset=d, subjects=[subject], return_epochs=True
                )
                for sm in tqdm(spectral_met, desc="met"):
                    ft = FunctionalTransformer(
                        delta=1, ratio=0.5, method=sm, fmin=fmin, fmax=fmax
                    )
                    preproc = Pipeline(steps=[("ft", ft), ("spd", EnsureSPD())])
                    data_fc[f][subject][sm] = preproc.fit_transform(ep_)
        with gzip.open(precomp_name, "w") as f:
            pickle.dump(data_fc, f)

    print("\n\n\n#################\nCompute results\n#################")
    dataset_res = list()
    for f in freqbands:
        fmin = freqbands[f][0]
        fmax = freqbands[f][1]
        subjects = subj
        for subject in tqdm(subjects, desc="subject"):
            print()
            fmin = freqbands["defaultBand"][0]
            fmax = freqbands["defaultBand"][1]
            # paradigm = LeftRightImagery(fmin=fmin, fmax=fmax)
            list_chann = dict_list_chann[str(subject)]
            paradigm = MotorImagery(events=events, n_classes=len(events), fmin=fmin, fmax=fmax, channels=list_chann)
            ep_, _, _ = paradigm.get_data(
                dataset=d, subjects=[subj[1]], return_epochs=True
            )
            nchan = ep_.info["nchan"]
            nb_nodes = [int(p / 100.0 * nchan) for p in percent_nodes]

            ppl_noDR, ppl_ens, baseline_ppl = {}, {}, {}
            # ppl_fewFC = {}
            ppl_DR = {}
            gd = GetDataMemory(subject, f, "cov", data_fc)
            baseline_ppl["TRCSP+LDA"] = Pipeline(steps=[("gd", gd)] + step_trcsp)
            baseline_ppl["RegCSP+shLDA"] = Pipeline(steps=[("gd", gd)] + step_regcsp)
            baseline_ppl["CSP+optSVM"] = Pipeline(steps=[("gd", gd)] + step_csp)
            baseline_ppl["FgMDM"] = Pipeline(steps=[("gd", gd)] + step_mdm)
            for sm in spectral_met:
                gd = GetDataMemory(subject, f, sm, data_fc)
                ft = FunctionalTransformer(
                    delta=1, ratio=0.5, method=sm, fmin=fmin, fmax=fmax
                )
                if sm == "cov":
                    ppl_DR["cov+elasticnet"] = Pipeline(
                        steps=[("gd", gd)] + step_cov
                    )
                    ppl_noDR["cov+elasticnet"] = Pipeline(
                        steps=[("gd", gd)] + step_cov
                    )
                else:
                    fname = (
                            path_data_root
                            + f"/opt-DR-ch_select-{subject}_{sm}-{threshold[0]}.npz"
                    )
                    ft_DR = FC_DimRed(
                        threshold=threshold,
                        nb_nodes=nb_nodes,
                        classifier=FgMDM(metric="riemann", tsupdate=False),
                        save_ch_fname=fname,
                    )
                    pname_postDR = sm + "+DR+elasticnet"
                    ppl_DR[pname_postDR] = Pipeline(
                        steps=[
                            ("gd", gd),
                            ("DR", ft_DR),
                        ]
                        + step_fc
                    )
                    pname_noDR = sm + "+elasticnet"
                    ppl_noDR[pname_noDR] = Pipeline(
                        steps=[("gd", gd)] + step_fc
                    )



            ################ Ensemble from single features classif with elasticnet ################
            DR_estimators = [(n, ppl_DR[n]) for n in ppl_DR]
            noDR_estimators = [(n, ppl_noDR[n]) for n in ppl_noDR]
            cvkf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

            # ensemble with elasticnet
            elastic_estimator = LogisticRegression(
                penalty="elasticnet",
                l1_ratio=0.15,
                intercept_scaling=1000.0,
                solver="saga",
            )
            scl_elastic_DR = StackingClassifier(
                estimators=DR_estimators,
                cv=cvkf,
                n_jobs=1,
                final_estimator=elastic_estimator,
                stack_method="predict_proba",
            )
            ppl_ens["ensemble-DR"] = scl_elastic_DR
            scl_elastic_noDR = StackingClassifier(
                estimators=noDR_estimators,
                cv=cvkf,
                n_jobs=1,
                final_estimator=elastic_estimator,
                stack_method="predict_proba",
            )
            ppl_ens["ensemble-noDR"] = scl_elastic_noDR

            all_ppl = {**baseline_ppl, **ppl_ens}
            #all_ppl = {**ppl_ens}

            ###########################################################################
            # Train and evaluate
            _, y, metadata = paradigm.get_data(d, [subject], return_epochs=True)
            X = np.arange(len(y))
            for session in np.unique(metadata.session):
                for ppn, ppl in tqdm(
                    all_ppl.items(), total=len(all_ppl), desc="pipelines"
                ):
                    ix = metadata.session == session
                    cv = StratifiedKFold(5, shuffle=True, random_state=42)
                    le = LabelEncoder()
                    y_cv = le.fit_transform(y[ix])
                    X_ = X[ix]
                    y_ = y_cv
                    for idx, (train, test) in enumerate(cv.split(X_, y_)):
                        cvclf = clone(ppl)
                        cvclf.fit(X_[train], y_[train])
                        yp = cvclf.predict(X_[test])
                        acc = balanced_accuracy_score(y_[test], yp)
                        # auc = roc_auc_score(y_[test], yp)
                        # kapp = cohen_kappa_score(y_[test], yp)
                        res_info = {
                            "subject": subject,
                            "session": "session_0",
                            "channels": nchan,
                            "n_sessions": 1,
                            "FreqBand": "defaultBand",
                            "dataset": d.code.replace(" ", "-"),
                            "fmin": fmin,
                            "fmax": fmax,
                            "samples": len(y_),
                            "time": 0.0,
                            "split": idx,
                        }
                        res = {
                            "score": acc,
                            # "kappa": kapp,
                            # "accuracy": acc,
                            "pipeline": ppn,
                            "n_dr": nchan,
                            "thres": 0,
                            **res_info,
                        }
                        dataset_res.append(res)
                        if isinstance(ppl, StackingClassifier):
                            for est_n, est_p in cvclf.named_estimators_.items():
                                p = est_p.get_params()
                                for step_est in p["steps"]:
                                    if isinstance(step_est[1], FC_DimRed):
                                        thres, n_dr = p[step_est[0]].best_param_
                                        break
                                else:
                                    thres, n_dr = 0, nchan
                                ype = est_p.predict(X_[test])
                                acc = balanced_accuracy_score(y_[test], ype)
                                # auc = roc_auc_score(y_[test], ype)
                                # kapp = cohen_kappa_score(y_[test], ype)
                                res = {
                                    "score": acc,
                                    # "kappa": kapp,
                                    # "accuracy": acc,
                                    "pipeline": est_n,
                                    "thres": thres,
                                    "n_dr": n_dr,
                                    **res_info,
                                }
                                dataset_res.append(res)
    dataset_res = pd.DataFrame(dataset_res)
    dataset_res.to_csv(
        path_csv_root + "/OptEnsemble-coreFC-allsubject-memory-2class-rf-invertloop-DR_IndivPreselectPaper_PatientA.csv"
    )
    print("saving " + path_csv_root + "/OptEnsemble-coreFC-allsubject-memory-2class-rf-invertloop-DR_IndivPreselectPaper_PatientA.csv")