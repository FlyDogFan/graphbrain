package com.graphbrain.webapp


import unfiltered.request._
import unfiltered.response._
import unfiltered.netty._

import com.graphbrain.db.Edge
import com.graphbrain.utils.SimpleLog


object NodeActionsPlan extends cycle.Plan with cycle.SynchronousExecution with ServerErrorResponse with SimpleLog {
  var errorMessage: String = ""

  def nodeActionResponse(id: String, params: Map[String, Seq[String]], cookies: Map[String, Any], req: HttpRequest[Any]) = {
    errorMessage = ""

    val op = params("op")(0)

    if (op == "remove") {
      removeLinkOrNode(params, cookies, req)
    }

    val userNode = WebServer.getUser(cookies)
    val node = WebServer.graph.get(id)
    NodePage(WebServer.graph, node, userNode, WebServer.prod, req, cookies, errorMessage).response
  }

  def removeLinkOrNode(params: Map[String, Seq[String]], cookies: Map[String, Any], req: HttpRequest[Any]) = {
    val userNode = WebServer.getUser(cookies)
    val edgeString = params("edge")(0)
    
    val edge = Edge(edgeString)

    WebServer.store.delrel2(edge, userNode.id)

    // force consesnsus re-evaluation of affected edge
    WebServer.consensusActor ! edge

    WebServer.log(req, cookies, "REMOVE EDGE: " + edgeString)
    ldebug("REMOVE EDGE: " + edgeString, Console.CYAN)
  }

  def intent = {
    case req@POST(Path(Seg("node" :: n1 :: Nil)) & Params(params) & Cookies(cookies)) =>
      nodeActionResponse(n1, params, cookies, req)
    case req@POST(Path(Seg("node" :: n1 :: n2 :: Nil)) & Params(params) & Cookies(cookies)) =>
      nodeActionResponse(n1 + "/" + n2, params, cookies, req)
    case req@POST(Path(Seg("node" :: n1 :: n2 :: n3 :: Nil)) & Params(params) & Cookies(cookies)) =>
      nodeActionResponse(n1 + "/" + n2 + "/" + n3, params, cookies, req)
    case req@POST(Path(Seg("node" :: n1 :: n2 :: n3 :: n4 :: Nil)) & Params(params) & Cookies(cookies)) =>
      nodeActionResponse(n1 + "/" + n2 + "/" + n3 + "/" + n4, params, cookies, req)
    case req@POST(Path(Seg("node" :: n1 :: n2 :: n3 :: n4 :: n5 :: Nil)) & Params(params) & Cookies(cookies)) =>
      nodeActionResponse(n1 + "/" + n2 + "/" + n3 + "/" + n4 + "/" + n5, params, cookies, req)
  }
}
