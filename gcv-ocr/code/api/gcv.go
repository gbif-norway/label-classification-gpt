package gcv

import (
	"context"
	"fmt"
	"log"
	"os"

	vision "cloud.google.com/go/vision/apiv1"
	pb "google.golang.org/genproto/googleapis/cloud/vision/v1"
)

func SendToOCR(imageURL string) (*pb.AnnotateImageResponse, error) {
	ctx := context.Background()
	client, err := vision.NewImageAnnotatorClient(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to create client: %v", err)
	}
	defer client.Close()

	request := &pb.AnnotateImageRequest{
		Image: &pb.Image{
			Source: &pb.ImageSource{
				ImageUri: imageURL,
			},
		},
		Features: []*pb.Feature{
			{
				Type: pb.Feature_TEXT_DETECTION,
			},
		},
		ImageContext: &pb.ImageContext{
			LanguageHints: []string{"no", "la"},
		},
	}

	response, err := client.AnnotateImage(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to send image to OCR: %v", err)
	}

	return response, nil
}
