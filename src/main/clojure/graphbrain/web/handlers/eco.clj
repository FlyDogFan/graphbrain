(ns graphbrain.web.handlers.eco
  (:require [graphbrain.db.gbdb :as gb]
            [graphbrain.db.id :as id]
            [graphbrain.db.maps :as maps]
            [graphbrain.disambig.edgeguesser :as edg]
            [graphbrain.eco.eco :as eco]
            [graphbrain.eco.words :as words]
            [graphbrain.eco.parsers.chat :as chat]
            [graphbrain.web.common :as common]
            [graphbrain.web.contexts :as contexts]
            [graphbrain.web.cssandjs :as css+js]
            [graphbrain.web.views.eco :as ecop]))

(defn- js
  []
  (str "var ptype='eco';"))

(defn- sentence->result
  [user root sentence ctxts]
  (let
      [env {:root (maps/vertex->eid root) :user (:id user)}
       words (words/str->words sentence)
       results (eco/parse-words chat/chat words env)
       res (first results)]
    (if (id/edge? res)
      (let [edge-id (edg/guess common/gbdb res sentence ctxts)
            edge (maps/id->vertex edge-id)
            edge (assoc edge :score 1)]
        {:words words
         :res res
         :edge edge})
      {:words words
       :res res})))

(defn report
  [user sentence ctxts]
  (sentence->result user "graphbrain" sentence ctxts))

(defn handle-eco
  [request]
  (let
      [sentence ((request :form-params) "input-field")
       user (common/get-user request)
       ctxts (contexts/active-ctxts request user)
       title "Eco test"
       report (if sentence
                (report user sentence ctxts))]
    (ecop/page :title title
               :css-and-js (css+js/css+js)
               :user user
               :js (js)
               :report report)))
