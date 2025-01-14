import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";  // Import IAM module

export class DiscordBotLambdaStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Define Docker Lambda function
    const dockerFunction = new lambda.DockerImageFunction(this, "DockerFunction", {
      code: lambda.DockerImageCode.fromImageAsset("./src"),
      memorySize: 1024,
      timeout: cdk.Duration.seconds(30), // Increased timeout to 30 seconds for longer operations
      architecture: lambda.Architecture.ARM_64,
      environment: {
        DISCORD_PUBLIC_KEY: "78b1af6f9ddc2ca3c2d18ccd01d23b47d318c48e1af65b078f95ea54d0ecbc82",
        OPENSEARCH_ENDPOINT: "https://search-mydomain-iqx6z4zm2bmohbfuxbevlqpqwm.aos.us-east-1.on.aws",
      },
    });

    // Create an IAM role for the Lambda function
    const role = new iam.Role(this, "LambdaRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
    });

    // Add managed policy for OpenSearch access
    role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonOpenSearchServiceFullAccess")
    );

    // Add custom inline policy for OpenSearch permissions
    dockerFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["es:*"],
        resources: [
          "arn:aws:es:us-east-1:761018848811:domain/mydomain/*", // Update with actual OpenSearch domain ARN
        ],
      })
    );

    // Expose the Lambda function URL
    const functionUrl = dockerFunction.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      cors: {
        allowedOrigins: ["*"],
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
      },
    });

    // Output the Function URL
    new cdk.CfnOutput(this, "FunctionUrl", {
      value: functionUrl.url,
    });
  }
}
