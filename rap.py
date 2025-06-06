import requests

cookies = {
    '_gcl_au': '1.1.1408185962.1747831531',
    '_gd_visitor': '470c6bb6-117a-4fee-8975-d1e8e66ec735',
    '__variation__FFNewModalExperiment': '0.18',
    '__variation__FFPostSignupModalMarketplace': '0.67',
    '__variation__FFNewHero': '0.04',
    '__variation__FFNewOrgCreatePage': '0.48',
    '__variation__FFAskCompanyInfo': '0.47',
    '__variation__FFEmbedTeamsVideo': '0.82',
    '__variation__FFTeamsLandingPageOrgButtonText': '0.01',
    '__variation__FFOrgCreationWithUsersInvitaions': '0.69',
    '__variation__FFApiPlaygroundABTest': '0.65',
    '__variation__FF_SearchInput_PlaceHolder': '0.76',
    '__variation__FFSubscribeModalDirectNavToPricing': '0.02',
    '__variation__FFNewPricingPage': '0.33',
    '__variation__FFPricingPaymentsAdminsInvite': '0.68',
    '__variation__FFPricingPersonalNoOrg': '0.86',
    '__variation__FFTryItFreeBottomMPTeamsPage': '0.07',
    '__variation__FFFastSubscribeToFreePlanOnMarketplace': '0.67',
    '__variation__FFNewPaymentPage': '0.74',
    '__variation__FFNewMarketplaceHomepageContent': '0.18',
    '__variation__FFAPILimitModalExperiment': '0.03',
    '__stripe_mid': 'fd8cb6bf-8a59-4db1-87a9-265da1a3b5feba1a88',
    'signupDate': '1747831696009',
    'firstSubDate': '1747831767565',
    '__cflb': '02DiuHPSNb326nZUQB6NoY4qqsJaLefLQcV3GWxq9jTvC',
    '_csrf': '-sV3A-4EeTjWrvmVkZ-_HVQp',
    '_gid': 'GA1.2.889151463.1748193813',
    '_gd_session': 'ce94ffc0-3d13-47de-88fd-dd9ed384ab43',
    'AMP_TOKEN': '%24NOT_FOUND',
    '__stripe_sid': '9acc5651-043a-43fa-83a8-88f1393ef8fbf52fe7',
    'jwt_auth': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTA1NTA5NjYsIm1hc2hhcGVJZCI6IjY4MTYxOTIwZjRjYmFkMDAyN2I2NmQ0OCIsIm9yaWdpbl9zaXRlIjoiZGVmYXVsdCIsImVtYWlsIjoiYXNhcm1lZGlhMTQwM0BnbWFpbC5jb20iLCJpc0dvZE1vZGUiOmZhbHNlLCJpc0F1dGhlbnRpY2F0ZWRCeVNTTyI6ZmFsc2UsIndhc1Nlc3Npb25Jc3N1ZWQiOnRydWUsImlhdCI6MTc0ODE5OTY3MCwiZXhwIjoxNzU1OTc1NjcwfQ.JWLJsFm6-UMR3Z3Ax3hyIb28GlT6pjSXJWn63EU-g0I',
    'connect.sid': 's%3Ad5_HMchmz337SPK8j13GQn7-BC83s5n0.GiO1p9HeAExJV2317YbrtXXShpyL9VNPI6Xh517jg6g',
    'ajs_user_id': '68161920f4cbad0027b66d48',
    'ajs_anonymous_id': '71e1856b-1e26-4284-b1c9-3c3bf6ffc6d8',
    'rapidapi-context': '10550966',
    'theme': 'light',
    'developer-timezone-analytics': '{"timezone":"(Asia/Tehran)","offset":210,"text":"GMT+03:30 Iran Standard Time (Asia/Tehran)","offsetString":"GMT+03:30","index":46}',
    '__cf_bm': '0suwFu2.fTQEhCXkFVy5uKVopB1_Zv26504IpjQUgO0-1748201203-1.0.1.1-J4L7k7QOpHIXOOsRfh8britz336lGKtW2IU1Bw2_6SvffoZJWmQ_6VQD_Tyf2RrREgznppKN43Manl3UVBmVSLrY5mImK_t1dot7LKB4b5U',
    '_ga_KK5QQ6G7DK': 'GS2.1.s1748199649$o2$g1$t1748201251$j0$l0$h0',
    '_gali': 'radix-%3Ard1%3A',
    'cf_clearance': 'M91PwiTlgY3aEB9ce2VOE11knOAUCQEY6drvY8w7QmI-1748201779-1.2.1.1-Ank5Yu87NaznZaJQPsN8KZG08WC4Co3b336RlW9L_frx3oAaz.B8.YvoaJP1Fv9eTwARBwcpTEhTACarleX6ENeBDCv_HgGUGCnhBpJEatUt_Ju7ss9xrfTRoid4gPN0LUOqQus_um7kZlwtx82x91hqFbECTi0BQyWHUYVGOwnueAFhu90YKcyjRGEBLdn21DRd6Npa7Vd_3t4WoRTozxOz4793nfyXGw4EhbByAwjhEo3RKNW57KecJI31r0x5kngweiCOaXXx6e38JiWkxt.HTuM1XPgUZ.xey7Cv88ZASq2nWL8PwnkDOLYkbQipj2R_pfqhN.FA5KEap4OmLK0EDibnPIN8xiZlzHTmMZU',
    '_ga_59PN3QBQJP': 'GS2.1.s1748199647$o7$g1$t1748201779$j0$l0$h0',
    '_ga': 'GA1.1.980549123.1747831531',
    '_gat': '1',
}

headers = {
    'accept': '*/*',
    'accept-language': 'en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6',
    'content-type': 'application/json',
    'csrf-token': 'OKQXcS5W-uxULaNJzL3gw9bbv-qdgRq0b1Lc',
    'origin': 'https://rapidapi.com',
    'priority': 'u=1, i',
    'rapid-client': 'hub-service',
    'referer': 'https://rapidapi.com/console/10550966/analytics/my-subscriptions/playground?metric=calls',
    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    'x-correlation-id': '9a33f983-1e25-4b5a-a5ec-79b59822a240',
    'x-entity-id': '10550966',
    # 'cookie': '_gcl_au=1.1.1408185962.1747831531; _gd_visitor=470c6bb6-117a-4fee-8975-d1e8e66ec735; __variation__FFNewModalExperiment=0.18; __variation__FFPostSignupModalMarketplace=0.67; __variation__FFNewHero=0.04; __variation__FFNewOrgCreatePage=0.48; __variation__FFAskCompanyInfo=0.47; __variation__FFEmbedTeamsVideo=0.82; __variation__FFTeamsLandingPageOrgButtonText=0.01; __variation__FFOrgCreationWithUsersInvitaions=0.69; __variation__FFApiPlaygroundABTest=0.65; __variation__FF_SearchInput_PlaceHolder=0.76; __variation__FFSubscribeModalDirectNavToPricing=0.02; __variation__FFNewPricingPage=0.33; __variation__FFPricingPaymentsAdminsInvite=0.68; __variation__FFPricingPersonalNoOrg=0.86; __variation__FFTryItFreeBottomMPTeamsPage=0.07; __variation__FFFastSubscribeToFreePlanOnMarketplace=0.67; __variation__FFNewPaymentPage=0.74; __variation__FFNewMarketplaceHomepageContent=0.18; __variation__FFAPILimitModalExperiment=0.03; __stripe_mid=fd8cb6bf-8a59-4db1-87a9-265da1a3b5feba1a88; signupDate=1747831696009; firstSubDate=1747831767565; __cflb=02DiuHPSNb326nZUQB6NoY4qqsJaLefLQcV3GWxq9jTvC; _csrf=-sV3A-4EeTjWrvmVkZ-_HVQp; _gid=GA1.2.889151463.1748193813; _gd_session=ce94ffc0-3d13-47de-88fd-dd9ed384ab43; AMP_TOKEN=%24NOT_FOUND; __stripe_sid=9acc5651-043a-43fa-83a8-88f1393ef8fbf52fe7; jwt_auth=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTA1NTA5NjYsIm1hc2hhcGVJZCI6IjY4MTYxOTIwZjRjYmFkMDAyN2I2NmQ0OCIsIm9yaWdpbl9zaXRlIjoiZGVmYXVsdCIsImVtYWlsIjoiYXNhcm1lZGlhMTQwM0BnbWFpbC5jb20iLCJpc0dvZE1vZGUiOmZhbHNlLCJpc0F1dGhlbnRpY2F0ZWRCeVNTTyI6ZmFsc2UsIndhc1Nlc3Npb25Jc3N1ZWQiOnRydWUsImlhdCI6MTc0ODE5OTY3MCwiZXhwIjoxNzU1OTc1NjcwfQ.JWLJsFm6-UMR3Z3Ax3hyIb28GlT6pjSXJWn63EU-g0I; connect.sid=s%3Ad5_HMchmz337SPK8j13GQn7-BC83s5n0.GiO1p9HeAExJV2317YbrtXXShpyL9VNPI6Xh517jg6g; ajs_user_id=68161920f4cbad0027b66d48; ajs_anonymous_id=71e1856b-1e26-4284-b1c9-3c3bf6ffc6d8; rapidapi-context=10550966; theme=light; developer-timezone-analytics={"timezone":"(Asia/Tehran)","offset":210,"text":"GMT+03:30 Iran Standard Time (Asia/Tehran)","offsetString":"GMT+03:30","index":46}; __cf_bm=0suwFu2.fTQEhCXkFVy5uKVopB1_Zv26504IpjQUgO0-1748201203-1.0.1.1-J4L7k7QOpHIXOOsRfh8britz336lGKtW2IU1Bw2_6SvffoZJWmQ_6VQD_Tyf2RrREgznppKN43Manl3UVBmVSLrY5mImK_t1dot7LKB4b5U; _ga_KK5QQ6G7DK=GS2.1.s1748199649$o2$g1$t1748201251$j0$l0$h0; _gali=radix-%3Ard1%3A; cf_clearance=M91PwiTlgY3aEB9ce2VOE11knOAUCQEY6drvY8w7QmI-1748201779-1.2.1.1-Ank5Yu87NaznZaJQPsN8KZG08WC4Co3b336RlW9L_frx3oAaz.B8.YvoaJP1Fv9eTwARBwcpTEhTACarleX6ENeBDCv_HgGUGCnhBpJEatUt_Ju7ss9xrfTRoid4gPN0LUOqQus_um7kZlwtx82x91hqFbECTi0BQyWHUYVGOwnueAFhu90YKcyjRGEBLdn21DRd6Npa7Vd_3t4WoRTozxOz4793nfyXGw4EhbByAwjhEo3RKNW57KecJI31r0x5kngweiCOaXXx6e38JiWkxt.HTuM1XPgUZ.xey7Cv88ZASq2nWL8PwnkDOLYkbQipj2R_pfqhN.FA5KEap4OmLK0EDibnPIN8xiZlzHTmMZU; _ga_59PN3QBQJP=GS2.1.s1748199647$o7$g1$t1748201779$j0$l0$h0; _ga=GA1.1.980549123.1747831531; _gat=1',
}

json_data = {
    'query': 'query apiTrafficAnalyticsLogs($where: AnalyticsStatsLogsInput!, $orderBy: [AnalyticsStatsLogsSortingInput!], $pagination: PaginationInput) {\n  apiTrafficAnalyticsLogs(\n    where: $where\n    orderBy: $orderBy\n    pagination: $pagination\n  ) {\n    totalCount\n    nodes {\n      requestId\n      consumer {\n        name\n        username\n        slugifiedName\n        thumbnail\n        email\n      }\n      endpointRoute\n      endpointId\n      apiId\n      apiName\n      httpMethod\n      apiLatency\n      callTime\n      callTimeUTC\n      originCountryName\n      httpStatus\n      apiVersionName\n      isPayloadExist\n    }\n  }\n}',
    'variables': {
        'where': {
            'consumerIds': [
                '10550966',
            ],
            'projectIds': [
                '68161920f4cbad0027b66d4a',
            ],
            'fromDate': '2025-05-17T20:30:00.000Z',
            'toDate': '2025-05-25T19:36:19.825Z',
            'timeOffset': 0,
        },
        'orderBy': [
            {
                'by': 'DESC',
                'fieldName': 'DATE_TIME',
            },
        ],
        'pagination': {
            'first': 10,
            'after': '',
        },
    },
    'operationName': 'apiTrafficAnalyticsLogs',
}
import json
response = requests.post('https://rapidapi.com/gateway/graphql', cookies=cookies, headers=headers, json=json_data)
with open('rapid.json', 'w') as f:
    j = json.dumps(response.json(), indent=4, ensure_ascii=False)
    f.write(j)
print(response.json())
# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
#data = '{"query":"query apiTrafficAnalyticsLogs($where: AnalyticsStatsLogsInput!, $orderBy: [AnalyticsStatsLogsSortingInput!], $pagination: PaginationInput) {\\n  apiTrafficAnalyticsLogs(\\n    where: $where\\n    orderBy: $orderBy\\n    pagination: $pagination\\n  ) {\\n    totalCount\\n    nodes {\\n      requestId\\n      consumer {\\n        name\\n        username\\n        slugifiedName\\n        thumbnail\\n        email\\n      }\\n      endpointRoute\\n      endpointId\\n      apiId\\n      apiName\\n      httpMethod\\n      apiLatency\\n      callTime\\n      callTimeUTC\\n      originCountryName\\n      httpStatus\\n      apiVersionName\\n      isPayloadExist\\n    }\\n  }\\n}","variables":{"where":{"consumerIds":["10550966"],"projectIds":["68161920f4cbad0027b66d4a"],"fromDate":"2025-05-17T20:30:00.000Z","toDate":"2025-05-25T19:36:19.825Z","timeOffset":0},"orderBy":[{"by":"DESC","fieldName":"DATE_TIME"}],"pagination":{"first":10,"after":""}},"operationName":"apiTrafficAnalyticsLogs"}'
#response = requests.post('https://rapidapi.com/gateway/graphql', cookies=cookies, headers=headers, data=data)