# --- Route53 Hosted Zone ---
# If you registered the domain via Route53, this is auto-created.
# If you bought it elsewhere, import it or create and update nameservers.
data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

# --- ACM Certificate for API (ALB) ---
resource "aws_acm_certificate" "api" {
  domain_name               = "api.${var.domain_name}"
  subject_alternative_names = [var.domain_name, "*.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "api_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
}

resource "aws_acm_certificate_validation" "api" {
  certificate_arn         = aws_acm_certificate.api.arn
  validation_record_fqdns = [for record in aws_route53_record.api_cert_validation : record.fqdn]
}

# --- ACM Certificate for CloudFront (must be in us-east-1) ---
resource "aws_acm_certificate" "cdn" {
  provider          = aws.us_east_1
  domain_name       = "app.${var.domain_name}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "cdn_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.cdn.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
}

resource "aws_acm_certificate_validation" "cdn" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.cdn.arn
  validation_record_fqdns = [for record in aws_route53_record.cdn_cert_validation : record.fqdn]
}

# --- DNS Records ---
# App subdomain → CloudFront (React product app)
resource "aws_route53_record" "app" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "app.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}

# Apex unipaith.co → Vercel anycast (Claude Design landing on Vercel).
# Replaces the prior ALB → WordPress target. Vercel apex IPs:
#   https://vercel.com/docs/projects/domains/working-with-domains#apex-domains
resource "aws_route53_record" "apex" {
  zone_id         = data.aws_route53_zone.main.zone_id
  name            = var.domain_name
  type            = "A"
  allow_overwrite = true
  ttl             = 300
  records         = ["76.76.21.142", "66.33.60.66"]
}

# www.unipaith.co → Vercel CNAME (canonical for non-apex)
resource "aws_route53_record" "www" {
  zone_id         = data.aws_route53_zone.main.zone_id
  name            = "www.${var.domain_name}"
  type            = "CNAME"
  allow_overwrite = true
  ttl             = 300
  records         = ["cname.vercel-dns.com"]
}

# API subdomain → ALB (for direct API access)
resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}
