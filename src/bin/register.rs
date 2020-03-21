use lambda_http::{lambda, IntoResponse, Request};
use lambda_runtime::{error::HandlerError, Context};
use serde_json::json;

fn main() {
    lambda!(handler)
}

fn handler(_request: Request, _ctx: Context) -> Result<impl IntoResponse, HandlerError> {
    let _guard = sentry::init("https://c28a0bbf11d443f98ef6253bdc29bbe6@sentry.io/5169580");
    sentry::integrations::panic::register_panic_handler();

    // `serde_json::Values` impl `IntoResponse` by default
    // creating an application/json response
    Ok(json!({
        "message": "user created"
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn creation_works() {
        let request = Request::default();
        let expected = json!({
            "message": "user created"
        })
        .into_response();
        let response = handler(request, Context::default())
            .expect("expected Ok(_) value")
            .into_response();
        assert_eq!(response.body(), expected.body())
    }
}
