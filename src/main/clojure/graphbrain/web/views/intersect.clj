(ns graphbrain.web.views.intersect
  (:use hiccup.core)
  (:require [graphbrain.web.views.barpage :as bar]))

(defn view
  [text]
  (html
   [:div {:id "data-view"}
    [:div {:id "inters-view"}]]))

(defn intersect
  [& {:keys [title css-and-js user js text]}]
  (bar/barpage :title title
               :css-and-js css-and-js
               :user user
               :js js
               :content-fun #(view text)))
